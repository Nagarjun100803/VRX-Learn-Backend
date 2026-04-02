from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Parameter, Table, functions
from pypika.dialects import PostgreSQLQuery
from pypika.terms import Criterion, ExistsCriterion, ValueWrapper

from src.command.commands.assignment_submissions import (
    AssignmentSubmission,
    AssignmentSubmissionContext,
    AssignmentSubmissionCreateWithAttemptAndStatus,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionGet,
    AssignmentSubmissionGetCore,
    AssignmentSubmissionVerifyWithStatus,
)
from src.command.commands.media import MediableType, MediaStatus
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.pypika_query_builder import PGSqlTypes, RowToJson


class AssignmentSubmissionRepository(BaseRepository[AssignmentSubmission]):
    tablename: ClassVar[str] = "assignment_submissions"

    def _to_domain(self, row: Optional[Record]) -> Optional[AssignmentSubmission]:
        if row is None:
            return None
        return AssignmentSubmission(**row)

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> AssignmentSubmission:
        cmd = self._normalize(cmd, AssignmentSubmissionCreateWithAttemptAndStatus)
        return await super().add(cmd, connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[AssignmentSubmission]:

        cmd = self._normalize_one_of(
            cmd,
            [AssignmentSubmissionVerifyWithStatus, AssignmentSubmissionFeedbackUpdate],
        )

        return await super().update(cmd, connection)

    async def delete(self, cmd, connection: Optional[Connection] = None):
        raise NotImplementedError("Deleting assignment submissions is not implemented")

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[AssignmentSubmission]:

        query = self._normalize_one_of(
            query, [AssignmentSubmissionGetCore, AssignmentSubmissionGet]
        )
        return await super().get(query, connection)

    async def count_attempts(self, user_id: int, assignment_id: int) -> int:
        """
        Count the number of attempts a user has made for a specific assignment.
            - Only counts attempts that have an associated media asset with status "UPLOADED".
            - This ensures that only valid attempts (where the user has successfully uploaded a submission) are counted.

        """
        table = Table(self.tablename)
        media_asset_table = Table("media_assets")

        submissions_subquery = (
            PostgreSQLQuery.from_(media_asset_table)
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == table.id,
                        media_asset_table.status == Parameter("$3"),
                        media_asset_table.mediable_type == Parameter("$4"),
                        media_asset_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(ValueWrapper(1))
        )

        sql = (
            PostgreSQLQuery.from_(table)
            .where(
                Criterion.all(
                    terms=[
                        table.created_by == Parameter("$1"),
                        table.assignment_id == Parameter("$2"),
                        table.deleted_at.isnull(),
                        ExistsCriterion(submissions_subquery),
                    ]
                )
            )
            .select(functions.Count("*").as_("number_of_attempts"))
        ).get_sql()

        executable = ExecutableSQL(
            sql,
            (
                user_id,
                assignment_id,
                MediableType.ASSIGNMENT_SUBMISSION,
                MediaStatus.UPLOADED,
            ),
        )

        result = await self.db.execute(executable, fetch_returns="one")

        return result["number_of_attempts"] if result else 0

    async def submission_context(
        self, submission_id: int
    ) -> Optional[AssignmentSubmissionContext]:
        """
        Get submission with assignment and media context.

        Submission and assignment are required.
        Media is optional (upload might fail).
        """

        assignment_submission_table = Table(self.tablename)
        media_asset_table = Table("media_assets")
        assignment_table = Table("assignments")

        sql = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .join(assignment_table)
            .on(assignment_table.id == assignment_submission_table.assignment_id)
            .left_join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == assignment_submission_table.id,
                        media_asset_table.mediable_type == Parameter("$1"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == Parameter("$2"),
                        assignment_submission_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                functions.Cast(
                    RowToJson(assignment_submission_table), PGSqlTypes.JSONB
                ).as_("submission"),
                functions.Cast(RowToJson(assignment_table), PGSqlTypes.JSONB).as_(
                    "assignment"
                ),
                functions.Cast(RowToJson(media_asset_table), PGSqlTypes.JSONB).as_(
                    "media"
                ),
            )
        ).get_sql()

        executable = ExecutableSQL(
            sql, (MediableType.ASSIGNMENT_SUBMISSION, submission_id)
        )

        result = await self.db.execute(executable, fetch_returns="one")

        if result is None:
            return None
        return AssignmentSubmissionContext.model_validate(result)
