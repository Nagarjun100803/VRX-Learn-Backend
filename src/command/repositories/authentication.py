from typing import Any, ClassVar, Optional

from asyncpg import Connection
from pypika import Criterion, Parameter, PostgreSQLQuery, Table, functions
from pypika.terms import ValueWrapper

from src.command.commands.authentication import PasswordReset
from src.command.commands.users import User
from src.database import AsyncPgDBManager, ExecutableSQL


class AuthenticationRepository:
    tablename: ClassVar[str] = "users"

    def __init__(self, db: AsyncPgDBManager):
        self.db = db

    async def update_last_login(
        self, user_id: int, connection: Optional[Connection] = None
    ) -> None:

        table = Table(self.tablename)

        update_query = (
            PostgreSQLQuery.update(table)
            .set("last_login", functions.Now())
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$1"), table.deleted_at.isnull()]
                )
            )
        )

        update_query: Any = update_query.returning("*")
        sql: str = update_query.get_sql()

        executable = ExecutableSQL(sql, (user_id,))

        await self.db.execute(executable, fetch_returns="one", connection=connection)

    async def reset_password(
        self, cmd: PasswordReset, connection: Optional[Connection] = None
    ) -> Optional[User]:

        table = Table(self.tablename)
        query = (
            PostgreSQLQuery.update(table)
            .set(table.password, Parameter("$1"))
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$2"), table.deleted_at.isnull()]
                )
            )
        )

        query: Any = query.returning("*")
        sql: str = query.get_sql()

        executable = ExecutableSQL(sql, (cmd.password, cmd.id))

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return User.model_validate(dict(result)) if result is not None else None

    async def update_email_verified(
        self, user_id: int, connection: Optional[Connection] = None
    ) -> Optional[User]:

        table = Table(self.tablename)

        query = (
            PostgreSQLQuery.update(table)
            .set(table.email_verified, ValueWrapper(True))
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$1"), table.deleted_at.isnull()]
                )
            )
        )

        query: Any = query.returning("*")
        sql: str = query.get_sql()

        executable = ExecutableSQL(sql, (user_id,))

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return User.model_validate(dict(result)) if result is not None else None
