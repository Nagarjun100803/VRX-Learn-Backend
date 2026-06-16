from typing import Any, ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Parameter, Table, functions
from pypika.dialects import PostgreSQLQuery
from pypika.terms import Criterion, ExistsCriterion, ValueWrapper

from src.command.commands.assignment_submissions import (
    AssignmentSubmission,
    AssignmentSubmissionCreateWithAttemptAndStatus,
    AssignmentSubmissionDetailContext,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionGet,
    AssignmentSubmissionGetCore,
    AssignmentSubmissionVerifyWithStatus,
    AssignmentSubmissionWithMedia,
)
from src.command.commands.media import MediableType, MediaStatus
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.query_builder import (
    PGSqlTypes,
    RowToJson,
    assignment_submission_table,
    media_asset_table,
)


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

    async def _delete_assignment_submission(
        self,
        assignment_submission_id: int,
        deleted_by: int,
        connection: Optional[Connection] = None,
    ) -> Optional[AssignmentSubmission]:

        # Delete the assignment submission.
        delete_assignment_submission_query = (
            PostgreSQLQuery.update(assignment_submission_table)
            .set(assignment_submission_table.deleted_at, functions.Now())
            .set(assignment_submission_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == Parameter("$1"),
                        assignment_submission_table.deleted_at.isnull(),
                    ]
                )
            )
        ).get_sql()

        # Delete media associated with the assignment submission.
        delete_assignment_submission_media_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == Parameter("$1"),
                        media_asset_table.mediable_type == Parameter("$3"),
                    ]
                )
            )
        ).get_sql()

        delete_assignment_submission_query: Any = (
            delete_assignment_submission_query.returning("*")
        )
        delete_assignment_submission_sql: str = (
            delete_assignment_submission_query.get_sql()
        )

        executable1 = ExecutableSQL(
            sql=delete_assignment_submission_sql,
            values=(assignment_submission_id, deleted_by),
        )
        executable2 = ExecutableSQL(
            sql=delete_assignment_submission_media_sql,
            values=(
                assignment_submission_id,
                deleted_by,
                MediableType.ASSIGNMENT_SUBMISSION,
            ),
        )

        async with self.db.transaction() as connection:
            await self.db.execute(
                executable2, fetch_returns="none", connection=connection
            )
            deleted_assignment_submission = await self.db.execute(
                executable1, fetch_returns="one", connection=connection
            )

            return self._to_domain(deleted_assignment_submission)

    async def delete(self, cmd, connection: Optional[Connection] = None):
        raise NotImplementedError("Deleting assignment submissions is not implemented")

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[AssignmentSubmission]:

        query = self._normalize_one_of(
            query, [AssignmentSubmissionGetCore, AssignmentSubmissionGet]
        )
        return await super().get(query, connection)

    async def get_with_media(
        self, query: AssignmentSubmissionGet, connection: Optional[Connection] = None
    ) -> Optional[AssignmentSubmissionWithMedia]:

        query = self._normalize(query, AssignmentSubmissionGet)

        assignment_submission_table = Table(self.tablename)
        media_asset_table = Table("media_assets")
        user_table = Table("users")
        assignment_table = Table("assignments")

        sql = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .join(assignment_table)
            .on(assignment_table.id == assignment_submission_table.assignment_id)
            .join(user_table)
            .on(assignment_submission_table.created_by == user_table.id)
            .join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == media_asset_table.mediable_id,
                        media_asset_table.status == Parameter("$1"),
                        media_asset_table.mediable_type == Parameter("$2"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == Parameter("$3"),
                        assignment_submission_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                        assignment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                assignment_submission_table.id,
                assignment_submission_table.assignment_id,
                assignment_submission_table.status,
                assignment_submission_table.score,
                assignment_table.max_score,
                assignment_submission_table.feedback,
                assignment_submission_table.attempt,
                assignment_submission_table.created_at.as_("submitted_at"),
                assignment_submission_table.created_by.as_("submitted_by"),
                user_table.username.as_("submitter_name"),
                media_asset_table.id.as_("media_id"),
                media_asset_table.mime_type,
                media_asset_table.filename,
            )
        ).get_sql()

        executable = ExecutableSQL(
            sql=sql,
            values=(MediaStatus.UPLOADED, MediableType.ASSIGNMENT_SUBMISSION, query.id),
        )

        result = await self.db.execute(executable, fetch_returns="one")

        if result is None:
            return None

        return AssignmentSubmissionWithMedia.model_validate(dict(result))

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
                MediaStatus.UPLOADED,
                MediableType.ASSIGNMENT_SUBMISSION,
            ),
        )

        result = await self.db.execute(executable, fetch_returns="one")

        return result["number_of_attempts"] if result else 0

    async def submission_context(
        self, submission_id: int
    ) -> Optional[AssignmentSubmissionDetailContext]:
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

        return AssignmentSubmissionDetailContext.model_validate(dict(result))
