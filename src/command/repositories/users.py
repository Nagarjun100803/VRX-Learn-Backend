from typing import Any, ClassVar, Optional, override

from asyncpg import Connection
from asyncpg.protocol.record import Record
from pydantic import BaseModel
from pypika import Parameter, PostgreSQLQuery, Table, functions
from pypika.terms import Criterion

from src.command.commands.base import ID
from src.command.commands.users import (
    PasswordUpdate,
    User,
    UserCreate,
    UserDelete,
    UserGetByEmail,
    UserGetByID,
)
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL


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

        cmd = self._normalize(cmd, PasswordUpdate)
        return await super().update(cmd, connection)

    @override
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[User]:

        cmd = self._normalize(cmd, UserDelete)

        return await super().delete(cmd, connection=connection)

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
