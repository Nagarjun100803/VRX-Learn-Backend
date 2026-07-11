from typing import Optional, cast

from pypika import Parameter, PostgreSQLQuery, Table, functions
from pypika import functions as fn
from pypika.terms import Criterion

from src.command.commands.media import MediableType, MediaStatus
from src.database import ExecutableSQL
from src.query.dto.course_overview import (
    CoursePreview,
    TraineeCourseOverview,
    TrainerCourseOverview,
)
from src.query.repositories.base import BaseQueryRepository, map_to_dto

from src.query_builder import (
    JsonbAgg,
    JsonbBuildObject,
    PGSqlTypes,
    assignment_table,
    course_table,
    enrollment_table,
    lesson_table,
    media_asset_table,
    module_table,
    user_table,
)


class TraineeCoursePreviewQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=CoursePreview, dto_mode="single")
    async def preview(self, course_id: int) -> Optional[CoursePreview]:
        lessons_subquery = (
            PostgreSQLQuery.from_(lesson_table)
            .join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == lesson_table.id,
                        media_asset_table.mediable_type == MediableType.LESSON,
                        media_asset_table.status == MediaStatus.UPLOADED,
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        lesson_table.module_id
                        == module_table.id,  # <= Refer from outer query.
                        lesson_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                JsonbAgg(
                    JsonbBuildObject(
                        "id",
                        lesson_table.id,
                        "title",
                        lesson_table.title,
                        "is_preview",
                        lesson_table.is_preview,
                        "mime_type",
                        media_asset_table.mime_type,
                    )
                ).orderby(module_table.position_string)
            )
        )

        modules_subquery = (
            PostgreSQLQuery.from_(module_table)
            .where(
                Criterion.all(
                    terms=[
                        module_table.course_id
                        == course_table.id,  # <= Refer from outer query.
                        module_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                JsonbAgg(
                    JsonbBuildObject(
                        "id",
                        module_table.id,
                        "title",
                        module_table.title,
                        "lessons",
                        functions.Coalesce(
                            lessons_subquery, functions.Cast("[]", PGSqlTypes.JSONB)
                        ),
                    )
                )
            )
        )

        course_preview_query = (
            PostgreSQLQuery.from_(course_table)
            .join(user_table)
            .on(user_table.id == course_table.trainer_id)
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$1"),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                JsonbBuildObject(
                    "id",
                    course_table.id,
                    "title",
                    course_table.title,
                    "description",
                    course_table.short_description,
                    "trainer",
                    user_table.username,
                ).as_("course"),
                functions.Coalesce(
                    modules_subquery, functions.Cast("[]", PGSqlTypes.JSONB)
                ).as_("modules"),
            )
        ).get_sql()

        executable = ExecutableSQL(sql=course_preview_query, values=(course_id,))

        return cast(
            Optional[CoursePreview], await self.db.execute(executable, fetch_returns="one")
        )


class QueryFactory:
    module_count_query = (
        PostgreSQLQuery.from_(module_table)
        .where(module_table.deleted_at.isnull())
        .groupby(module_table.course_id)
        .select(
            module_table.course_id,  # To join with course_table
            fn.Count(module_table.id).distinct().as_("no_of_modules"),
        )
    )

    lesson_count_query = (
        PostgreSQLQuery.from_(lesson_table)
        .join(module_table)
        .on(lesson_table.module_id == module_table.id)
        .join(media_asset_table)
        .on(
            Criterion.all(
                terms=[
                    media_asset_table.mediable_id == lesson_table.id,
                    media_asset_table.mediable_type == Parameter("$1"),
                    media_asset_table.status == Parameter("$2"),
                ]
            )
        )
        .where(
            Criterion.all(
                terms=[
                    lesson_table.deleted_at.isnull(),
                    media_asset_table.deleted_at.isnull(),
                ]
            )
        )
        .groupby(module_table.course_id)
        .select(
            module_table.course_id,
            fn.Count(lesson_table.id).distinct().as_("no_of_lessons"),
        )
    )

    assignment_count_query = (
        PostgreSQLQuery.from_(assignment_table)
        .left_join(media_asset_table)
        .on(
            Criterion.all(
                terms=[
                    media_asset_table.mediable_id == assignment_table.id,
                    media_asset_table.mediable_type == Parameter("$3"),
                ]
            )
        )
        .where(
            Criterion.all(
                terms=[
                    assignment_table.deleted_at.isnull(),
                    media_asset_table.deleted_at.isnull(),
                    Criterion.any(
                        terms=[
                            media_asset_table.id.isnull(),
                            media_asset_table.status == Parameter("$2"),
                        ]
                    ),
                ]
            )
        )
        .groupby(assignment_table.course_id)
        .select(
            assignment_table.course_id,
            fn.Count(assignment_table.id).distinct().as_("no_of_assignments"),
        )
    )

    trainee_count_query = (
        PostgreSQLQuery.from_(enrollment_table)
        .where(
            Criterion.all(
                terms=[
                    enrollment_table.course_id == Parameter("$4"),
                    enrollment_table.deleted_at.isnull(),
                ]
            )
        )
        .groupby(enrollment_table.course_id)
        .select(
            enrollment_table.course_id,
            fn.Count(enrollment_table.id).distinct().as_("no_of_trainees"),
        )
    )


class TraineeCourseOverviewQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TraineeCourseOverview, dto_mode="single")
    async def course_overview(self, course_id: int) -> Optional[TraineeCourseOverview]:

        # reference tables.
        lesson_count_cte = Table("lesson_count_cte")
        assignment_count_cte = Table("assignment_count_cte")
        module_count_cte = Table("module_count_cte")

        sql = (
            PostgreSQLQuery.with_(
                QueryFactory.lesson_count_query, lesson_count_cte._table_name
            )
            .with_(QueryFactory.module_count_query, module_count_cte._table_name)
            .with_(
                QueryFactory.assignment_count_query, assignment_count_cte._table_name
            )
            .from_(course_table)
            .join(user_table)
            .on(course_table.trainer_id == user_table.id)
            .left_join(module_count_cte)
            .on(module_count_cte.course_id == course_table.id)
            .left_join(assignment_count_cte)
            .on(assignment_count_cte.course_id == course_table.id)
            .left_join(lesson_count_cte)
            .on(lesson_count_cte.course_id == course_table.id)
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$4"),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                course_table.id.as_("course_id"),
                course_table.title,
                course_table.short_description,
                user_table.username.as_("trainer_name"),
                fn.Coalesce(module_count_cte.no_of_modules, 0).as_("no_of_modules"),
                fn.Coalesce(assignment_count_cte.no_of_assignments, 0).as_(
                    "no_of_assignments"
                ),
                fn.Coalesce(lesson_count_cte.no_of_lessons, 0).as_("no_of_lessons"),
            )
        ).get_sql()

        executable = ExecutableSQL(
            sql=sql,
            values=(
                MediableType.LESSON,
                MediaStatus.UPLOADED,
                MediableType.ASSIGNMENT,
                course_id,
            ),
        )

        return cast(
            Optional[TraineeCourseOverview],
            await self.db.execute(executable, fetch_returns="one"),
        )


class TrainerCourseOverviewQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TrainerCourseOverview, dto_mode="single")
    async def course_overview(self, course_id: int) -> Optional[TrainerCourseOverview]:

        lesson_count_cte = Table("lesson_count_cte")
        assignment_count_cte = Table("assignment_count_cte")
        module_count_cte = Table("module_count_cte")
        trainee_count_cte = Table("trainee_count_cte")

        sql = (
            PostgreSQLQuery.with_(
                QueryFactory.lesson_count_query, lesson_count_cte._table_name
            )
            .with_(QueryFactory.module_count_query, module_count_cte._table_name)
            .with_(
                QueryFactory.assignment_count_query, assignment_count_cte._table_name
            )
            .with_(QueryFactory.trainee_count_query, trainee_count_cte._table_name)
            .from_(course_table)
            .join(user_table)
            .on(course_table.trainer_id == user_table.id)
            .left_join(module_count_cte)
            .on(module_count_cte.course_id == course_table.id)
            .left_join(assignment_count_cte)
            .on(assignment_count_cte.course_id == course_table.id)
            .left_join(lesson_count_cte)
            .on(lesson_count_cte.course_id == course_table.id)
            .left_join(trainee_count_cte)
            .on(trainee_count_cte.course_id == course_table.id)
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$4"),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                course_table.id.as_("course_id"),
                course_table.title,
                course_table.short_description,
                user_table.username.as_("trainer_name"),
                fn.Coalesce(module_count_cte.no_of_modules, 0).as_("no_of_modules"),
                fn.Coalesce(assignment_count_cte.no_of_assignments, 0).as_(
                    "no_of_assignments"
                ),
                fn.Coalesce(lesson_count_cte.no_of_lessons, 0).as_("no_of_lessons"),
                fn.Coalesce(trainee_count_cte.no_of_trainees, 0).as_("no_of_trainees"),
            )
        ).get_sql()

        executable = ExecutableSQL(
            sql=sql,
            values=(
                MediableType.LESSON,
                MediaStatus.UPLOADED,
                MediableType.ASSIGNMENT,
                course_id,
            ),
        )

        return cast(
            Optional[TrainerCourseOverview],
            await self.db.execute(executable, fetch_returns="one"),
        )
