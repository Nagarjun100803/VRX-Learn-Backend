from typing import Any, ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Parameter, PostgreSQLQuery, functions
from pypika.terms import Criterion

from src.command.commands.assignments import (
    Assignment,
    AssignmentCreate,
    AssignmentDelete,
    AssignmentGet,
    AssignmentUpdate,
)
from src.command.commands.media import MediableType
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.query_builder import (
    assignment_submission_table,
    assignment_table,
    media_asset_table,
)


class AssignmentRepository(BaseRepository[Assignment]):
    tablename: ClassVar[str] = "assignments"

    def _to_domain(self, row: Optional[Record]) -> Optional[Assignment]:
        if row is None:
            return None
        return Assignment.model_validate(dict(row))

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Assignment:
        cmd = self._normalize(cmd, AssignmentCreate)
        return await super().add(cmd, connection=connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Assignment]:
        cmd = self._normalize(cmd, AssignmentUpdate)
        return await super().update(cmd, connection=connection)

    async def _delete_assignment_submissions(
        self, cmd: AssignmentDelete, connection: Optional[Connection] = None
    ) -> None:

        # Delete all assignment submissions
        assignment_submission_ids_subquery = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .where(assignment_submission_table.assignment_id == Parameter("$1"))
            .select(assignment_submission_table.id)
        )

        delete_assignment_submissions_sql = (
            PostgreSQLQuery.update(assignment_submission_table)
            .set(assignment_submission_table.deleted_at, functions.Now())
            .set(assignment_submission_table.deleted_by, Parameter("$2"))
            .where(
                assignment_submission_table.assignment_id.isin(
                    assignment_submission_ids_subquery
                )
            )
        ).get_sql()

        # Delete all media associated with those assignment submissions.
        delete_assignment_submissions_media_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_type == Parameter("$3"),
                        media_asset_table.mediable_id.isin(
                            assignment_submission_ids_subquery
                        ),
                    ]
                )
            )
        ).get_sql()

        executable1 = ExecutableSQL(
            sql=delete_assignment_submissions_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            sql=delete_assignment_submissions_media_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.ASSIGNMENT_SUBMISSION),
        )

        await self.db.execute(executable1, fetch_returns="none", connection=connection)
        await self.db.execute(executable2, fetch_returns="none", connection=connection)

    async def _delete_assignment(
        self, cmd: AssignmentDelete, connection: Optional[Connection] = None
    ) -> Optional[Assignment]:

        # Delete the assignment.
        delete_assignment_query = (
            PostgreSQLQuery.update(assignment_table)
            .set(assignment_table.deleted_at, functions.Now())
            .set(assignment_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.deleted_at.isnull(),
                        assignment_table.id == Parameter("$1"),
                    ]
                )
            )
        )

        # Delete media associated with that assignment.
        delete_assignment_media_sql = (
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

        delete_assignment_query: Any = delete_assignment_query.returning("*")  # type: ignore
        delete_assignment_sql: str = delete_assignment_query.get_sql()

        executable1 = ExecutableSQL(
            sql=delete_assignment_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            sql=delete_assignment_media_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.ASSIGNMENT),
        )

        await self.db.execute(executable2, fetch_returns="none", connection=connection)

        deleted_assignment = await self.db.execute(
            executable1, fetch_returns="one", connection=connection
        )

        return self._to_domain(deleted_assignment)

    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Assignment]:

        cmd = self._normalize(cmd, AssignmentDelete)

        async with self.db.transaction() as connection:
            await self._delete_assignment_submissions(cmd, connection=connection)
            return await self._delete_assignment(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Assignment]:
        query = self._normalize(query, AssignmentGet)
        return await super().get(query, connection=connection)
