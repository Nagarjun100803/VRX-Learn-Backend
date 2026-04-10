from typing import Optional, cast

from pypika import Case, Criterion, Parameter, PostgreSQLQuery, Table
from pypika import functions as fn
from pypika.terms import ExistsCriterion, ValueWrapper

from src.command.commands.media import MediableType, MediaStatus
from src.database import ExecutableSQL
from src.pypika_query_builder import (
    JsonbAgg,
    JsonbBuildObject,
    assignment_submission_table,
    assignment_table,
    media_asset_table,
)
from src.query.dto.assignment_contents import (
    TraineeAssignmentContent,
    TraineeAssignmentCore,
    TrainerAssignmentContent,
    TrainerAssignmentCore,
)
from src.query.repositories.base import BaseQueryRepository, map_to_dto


class TraineeAssignmentContentQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TraineeAssignmentCore, dto_mode="list")
    async def assignments(
        self, course_id: int, trainee_id: int
    ) -> list[TraineeAssignmentCore]:

        submissions_query = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.created_by == Parameter("$3"),
                        assignment_submission_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(assignment_submission_table.assignment_id)
        )  # Used inn where clause of a case statement.

        submission_cte = Table("submission_cte")  # Reference table

        sql = (
            PostgreSQLQuery.with_(submissions_query, submission_cte._table_name)
            .from_(assignment_table)
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == Parameter("$4"),
                        assignment_table.deleted_at.isnull(),
                    ]
                )
            )
            .orderby(assignment_table.due_date)
            .select(
                assignment_table.id,
                assignment_table.title,
                Case()
                .when(
                    ExistsCriterion(
                        PostgreSQLQuery.from_(submission_cte)
                        .where(submission_cte.assignment_id == assignment_table.id)
                        .select(ValueWrapper(1))
                    ),
                    ValueWrapper(True),
                )
                .else_(ValueWrapper(False))
                .as_("is_completed"),
            )
            .get_sql()
        )
        executable = ExecutableSQL(
            sql,
            (
                MediableType.ASSIGNMENT_SUBMISSION,
                MediaStatus.UPLOADED,
                trainee_id,
                course_id,
            ),
        )

        return cast(
            list[TraineeAssignmentCore],
            await self.db.execute(executable, fetch_returns="all"),
        )

    @map_to_dto(dto=TraineeAssignmentContent, dto_mode="single")
    async def assignment_contents(
        self, assignment_id: int, trainee_id: int
    ) -> Optional[TraineeAssignmentContent]:

        submissions_query = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.created_by == Parameter("$3"),
                        assignment_submission_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                assignment_submission_table.assignment_id,  # For filtering inside of main query.,
                assignment_submission_table.created_at,  # For ordering,
                JsonbBuildObject(
                    "id",
                    assignment_submission_table.id,
                    "filename",
                    media_asset_table.filename,
                    "score",
                    assignment_submission_table.score,
                    "status",
                    assignment_submission_table.status,
                    "attempt",
                    assignment_submission_table.attempt,
                    "submitted_at",
                    assignment_submission_table.created_at,
                    "media_id",
                    media_asset_table.id,
                ).as_("submission"),
            )
        )

        submission_cte = Table("submission_cte")  # Reference table

        sql = (
            PostgreSQLQuery.with_(submissions_query, submission_cte._table_name)
            .from_(assignment_table)
            .left_join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        assignment_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$4"),
                        media_asset_table.status == Parameter("$5"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.id == Parameter("$6"),
                        assignment_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                JsonbBuildObject(
                    "id",
                    assignment_table.id,
                    "title",
                    assignment_table.title,
                    "max_score",
                    assignment_table.max_score,
                    "number_of_attempts",
                    assignment_table.number_of_attempts,
                    "due_date",
                    assignment_table.due_date,
                    "instructions",
                    assignment_table.instructions,
                ).as_("assignment"),
                Case()
                .when(
                    media_asset_table.id.isnotnull(),
                    JsonbBuildObject(
                        "media_id",
                        media_asset_table.id,
                        "filename",
                        media_asset_table.filename,
                    ),
                )
                .else_(ValueWrapper(None))
                .as_("attachment"),
                PostgreSQLQuery.from_(submission_cte)
                .where(submission_cte.assignment_id == assignment_table.id)
                .select(
                    fn.Coalesce(
                        JsonbAgg(submission_cte.submission)
                        .filter(submission_cte.submission.isnotnull())
                        .orderby(submission_cte.created_at),
                        ValueWrapper("[]"),
                    ).as_("submissions")
                ),
            )
            .get_sql()
        )

        executable = ExecutableSQL(
            sql,
            (
                MediableType.ASSIGNMENT_SUBMISSION,
                MediaStatus.UPLOADED,
                trainee_id,
                MediableType.ASSIGNMENT,
                MediaStatus.UPLOADED,
                assignment_id,
            ),
        )
        return cast(
            Optional[TraineeAssignmentContent],
            await self.db.execute(executable, fetch_returns="one"),
        )


class TrainerAssignmentContentQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TrainerAssignmentCore, dto_mode="list")
    async def assignments(self, course_id: int) -> list[TrainerAssignmentCore]:

        sql = (
            PostgreSQLQuery.from_(assignment_table)
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == Parameter("$1"),
                        assignment_table.deleted_at.isnull(),
                    ]
                )
            )
            .orderby(assignment_table.due_date)
            .select(
                assignment_table.id, assignment_table.title, assignment_table.due_date
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql, (course_id,))

        return cast(
            list[TrainerAssignmentCore],
            await self.db.execute(executable, fetch_returns="all"),
        )

    @map_to_dto(dto=TrainerAssignmentContent, dto_mode="single")
    async def assignment_contents(
        self, assignment_id: int
    ) -> Optional[TrainerAssignmentContent]:

        sql = (
            PostgreSQLQuery.from_(assignment_table)
            .left_join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        assignment_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.id == Parameter("$3"),
                        assignment_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                JsonbBuildObject(
                    "id",
                    assignment_table.id,
                    "title",
                    assignment_table.title,
                    "max_score",
                    assignment_table.max_score,
                    "number_of_attempts",
                    assignment_table.number_of_attempts,
                    "due_date",
                    assignment_table.due_date,
                    "instructions",
                    assignment_table.instructions,
                ).as_("assignment"),
                Case()
                .when(
                    media_asset_table.id.isnotnull(),
                    JsonbBuildObject(
                        "media_id",
                        media_asset_table.id,
                        "filename",
                        media_asset_table.filename,
                    ),
                )
                .else_(ValueWrapper(None))
                .as_("attachment"),
            )
            .get_sql()
        )

        executable = ExecutableSQL(
            sql, values=(MediableType.ASSIGNMENT, MediaStatus.UPLOADED, assignment_id)
        )

        return cast(
            Optional[TraineeAssignmentContent],
            await self.db.execute(executable, fetch_returns="one"),
        )
