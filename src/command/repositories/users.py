from typing import Any, ClassVar, Optional, override

from asyncpg import Connection
from asyncpg.protocol.record import Record
from pydantic import BaseModel
from pypika import Parameter, PostgreSQLQuery, Table, functions
from pypika.terms import Criterion

from src.command.commands.base import ID
from src.command.commands.media import MediableType
from src.command.commands.users import (
    ResetPassword,
    User,
    UserCreate,
    UserDelete,
    UserGetByEmail,
    UserGetByID,
)
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.pypika_query_builder import (
    assignment_submission_table,
    enrollment_table,
    media_asset_table,
    user_table,
)


class UserRepository(BaseRepository[User]):
    tablename: ClassVar[str] = "users"

    @override
    def _to_domain(self, row: Optional[Record]) -> Optional[User]:
        if not row:
            return None
        return User.model_validate(dict(row))

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> User:
        cmd = self._normalize(cmd, UserCreate)
        return await super().add(cmd, connection)

    @override
    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[User]:

        cmd = self._normalize(cmd, ResetPassword)
        query = (
            PostgreSQLQuery.update(user_table)
            .set(user_table.password, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        user_table.id == Parameter("$1"),
                        user_table.deleted_at.isnull(),
                    ]
                )
            )
        )

        query: Any = query.returning("*")  # type: ignore
        sql: str = query.get_sql()

        executable = ExecutableSQL(sql=sql, values=(cmd.id, cmd.password))

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )
        return self._to_domain(result)

    async def _delete_enrollments(
        self, cmd: UserDelete, connection: Optional[Connection] = None
    ) -> None:

        delete_enrollment_sql = (
            PostgreSQLQuery.update(enrollment_table)
            .set(enrollment_table.deleted_at, functions.Now())
            .set(enrollment_table.deleted_by, Parameter("$2"))
            .where(enrollment_table.user_id == Parameter("$1"))
        ).get_sql()

        executable = ExecutableSQL(
            sql=delete_enrollment_sql, values=(cmd.id, cmd.deleted_by)
        )

        await self.db.execute(executable, fetch_returns="none", connection=connection)

    async def _delete_assignment_submissions(
        self, cmd: UserDelete, connection: Optional[Connection] = None
    ) -> None:

        assignment_submission_ids_subquery = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .where(assignment_submission_table.created_by == Parameter("$1"))
            .select(assignment_submission_table.id)
        )

        # Delete the assignment submissions created by the user.
        delete_assignment_submission_sql = (
            PostgreSQLQuery.update(assignment_submission_table)
            .set(assignment_submission_table.deleted_at, functions.Now())
            .set(assignment_submission_table.deleted_by, Parameter("$2"))
            .where(
                assignment_submission_table.id.isin(assignment_submission_ids_subquery)
            )
        ).get_sql()

        # Delete the media associated with those assignment submissions.
        delete_assignment_submission_media_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id.isin(
                            assignment_submission_ids_subquery
                        ),
                        media_asset_table.mediable_type == Parameter("$3"),
                    ]
                )
            )
        ).get_sql()

        executable1 = ExecutableSQL(
            sql=delete_assignment_submission_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            sql=delete_assignment_submission_media_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.ASSIGNMENT_SUBMISSION),
        )

        await self.db.execute(executable1, fetch_returns="none", connection=connection)
        await self.db.execute(executable2, fetch_returns="none", connection=connection)

    async def _delete_user(
        self, cmd: UserDelete, connection: Optional[Connection] = None
    ) -> Optional[User]:

        delete_user_query = (
            PostgreSQLQuery.update(user_table)
            .set(user_table.deleted_at, functions.Now())
            .set(user_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        user_table.id == Parameter("$1"),
                        user_table.deleted_at.isnull(),
                    ]
                )
            )
        )

        delete_user_query: Any = delete_user_query.returning("*")  # type: ignore
        delete_user_sql: str = delete_user_query.get_sql()

        executable = ExecutableSQL(sql=delete_user_sql, values=(cmd.id, cmd.deleted_by))

        deleted_user = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return self._to_domain(deleted_user)

    @override
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[User]:

        cmd = self._normalize(cmd, UserDelete)

        async with self.db.transaction() as connection:
            await self._delete_enrollments(cmd, connection=connection)
            await self._delete_assignment_submissions(cmd, connection=connection)

            return await self._delete_user(cmd, connection=connection)

    @override
    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[User]:

        query = self._normalize_one_of(query, [UserGetByID, UserGetByEmail])

        if isinstance(query, UserGetByID):
            return await super().get(query)

        table = Table(self.tablename)
        sql = (
            PostgreSQLQuery.from_(table)
            .select("*")
            .where(
                Criterion.all(
                    terms=[table.email == Parameter("$1"), table.deleted_at.isnull()]
                )
            )
        )
        executable = ExecutableSQL(sql.get_sql(), (query.email,))

        user = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return self._to_domain(user)

    async def update_last_login(self, user_id: ID) -> Optional[User]:

        table = Table(self.tablename)
        update_query = (
            PostgreSQLQuery.update(table)
            .set("last_login", functions.Now())
            .set("updated_by", user_id)
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$1"), table.deleted_at.isnull()]
                )
            )
        )

        update_query: Any = update_query.returning("*")
        sql: str = update_query.get_sql()

        executable = ExecutableSQL(sql, (user_id,))

        result = await self.db.execute(executable, fetch_returns="one")

        return self._to_domain(result)
