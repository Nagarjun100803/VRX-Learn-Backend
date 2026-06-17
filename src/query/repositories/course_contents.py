from typing import Optional, cast

from pypika import Case, Criterion, Parameter, PostgreSQLQuery, functions
from pypika.terms import ExistsCriterion, ValueWrapper

from src.command.commands.media import MediableType, MediaStatus
from src.database import ExecutableSQL
from src.query.dto.course_contents import TraineeCourseContent, TrainerCourseContent
from src.query.repositories.base import BaseQueryRepository, map_to_dto
from src.query_builder import (
    JsonbAgg,
    JsonbBuildObject,
    LateralQuery,
    PGJoinType,
    PGSqlTypes,
    assignment_table,
    course_table,
    enrollment_table,
    lesson_table,
    media_asset_table,
    module_restriction_table,
    module_table,
    user_table,
)


class TraineeCourseContentQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TraineeCourseContent, dto_mode="single")
    async def course_contents(
        self, course_id: int, user_id: int
    ) -> Optional[TraineeCourseContent]:

        lessons_subquery = (
            PostgreSQLQuery.from_(lesson_table)
            .join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        lesson_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == MediableType.LESSON,
                        media_asset_table.status == MediaStatus.UPLOADED,
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        lesson_table.module_id == module_table.id,
                        lesson_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                functions.Coalesce(
                    JsonbAgg(
                        JsonbBuildObject(
                            "id",
                            lesson_table.id,
                            "title",
                            lesson_table.title,
                            "description",
                            lesson_table.description,
                            "media_id",
                            media_asset_table.id,
                            "mime_type",
                            media_asset_table.mime_type,
                            "filename",
                            media_asset_table.filename,
                        )
                    ).orderby(lesson_table.position_string),
                    functions.Cast("[]", as_type=PGSqlTypes.JSONB),
                ).as_("lessons")
            )
        )

        modules_subquery = (
            PostgreSQLQuery.from_(module_table)
            .where(
                Criterion.all(
                    terms=[
                        module_table.deleted_at.isnull(),
                        module_table.course_id
                        == course_table.id,  # <- Call from outer query.
                    ]
                )
            )
            .select(
                functions.Coalesce(
                    JsonbAgg(
                        JsonbBuildObject(
                            "id",
                            module_table.id,
                            "title",
                            module_table.title,
                            "description",
                            module_table.description,
                            "restricted",
                            Case()
                            .when(
                                ExistsCriterion(
                                    PostgreSQLQuery.select(ValueWrapper(1))
                                    .from_(module_restriction_table)
                                    .where(
                                        Criterion.all(
                                            terms=[
                                                module_restriction_table.module_id
                                                == module_table.id,
                                                module_restriction_table.enrollment_id
                                                == enrollment_table.id,
                                            ]
                                        )
                                    )
                                ),
                                True,
                            )
                            .else_(False),
                            "lessons",
                            lessons_subquery,
                        )
                    ).orderby(module_table.position_string),
                    functions.Cast("[]", as_type=PGSqlTypes.JSONB),
                ).as_("modules")
            )
        )

        sql = (
            PostgreSQLQuery.from_(course_table)
            .join(enrollment_table)
            .on(enrollment_table.course_id == course_table.id)
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$1"),
                        enrollment_table.user_id == Parameter("$2"),
                        course_table.deleted_at.isnull(),
                        enrollment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                JsonbBuildObject(
                    "id",
                    course_table.id,
                    "title",
                    course_table.title,
                    "short_description",
                    course_table.short_description,
                ).as_("course"),
                modules_subquery,
            )
        )

        executable = ExecutableSQL(sql=sql.get_sql(), values=(course_id, user_id))

        return cast(
            Optional[TraineeCourseContent],
            await self.db.execute(executable, fetch_returns="one"),
        )


class TrainerCourseContentQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TrainerCourseContent, dto_mode="single")
    async def course_contents(self, course_id: int) -> Optional[TrainerCourseContent]:

        module_detail_subquery = (
            PostgreSQLQuery.from_(module_table)
            .where(
                Criterion.all(
                    terms=[
                        module_table.course_id
                        == course_table.id,  # For Outer table reference.
                        module_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                functions.Coalesce(
                    JsonbAgg(
                        JsonbBuildObject(
                            "id",
                            module_table.id,
                            "title",
                            module_table.title,
                            "description",
                            module_table.description,
                        )
                    )
                    .filter(module_table.id.isnotnull())
                    .orderby(module_table.position_string),
                    ValueWrapper("[]"),
                ).as_("modules")
            )
        )

        module_detail = LateralQuery(module_detail_subquery, alias="md")

        assignment_detail_subquery = (
            PostgreSQLQuery.from_(assignment_table)
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == course_table.id,
                        assignment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                functions.Coalesce(
                    JsonbAgg(
                        JsonbBuildObject(
                            "id", assignment_table.id, "title", assignment_table.title
                        )
                    )
                    .filter(assignment_table.id.isnotnull())
                    .orderby(assignment_table.due_date),
                    ValueWrapper("[]"),
                ).as_("assignments")
            )
        )

        assignment_detail = LateralQuery(assignment_detail_subquery, alias="ad")

        sql = (
            PostgreSQLQuery.from_(course_table)
            .join(user_table)
            .on(user_table.id == course_table.trainer_id)
            .join(module_detail, how=PGJoinType.left_lateral)  # type: ignore
            .on(ValueWrapper(True))  # type: ignore
            .join(assignment_detail, how=PGJoinType.left_lateral)  # type: ignore
            .on(ValueWrapper(True))  # type: ignore
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
                    "short_description",
                    course_table.short_description,
                    "long_description",
                    course_table.long_description,
                    "trainer_id",
                    course_table.trainer_id,
                    "trainer_name",
                    user_table.username,
                ).as_("course"),
                module_detail.modules,
                assignment_detail.assignments,
            )
            .get_sql()
            .replace("LATERAL JOIN", "LATERAL")
        )

        executable = ExecutableSQL(sql, values=(course_id,))

        return cast(
            Optional[TrainerCourseContent],
            await self.db.execute(executable, fetch_returns="one"),
        )
