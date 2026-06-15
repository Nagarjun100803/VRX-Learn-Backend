from typing import ClassVar, Optional

from asyncpg import Connection
from pypika import Criterion, Parameter, PostgreSQLQuery, Table

from src.command.commands.module_restrictions import (
    ModuleRestrictionCreate,
    ModuleRestrictionDelete,
)
from src.database import AsyncPgDBManager, ExecutableSQL


class ModuleRestrictionRepository:
    tablename: ClassVar[str] = "module_restriction"

    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db

    async def create(
        self, cmd: ModuleRestrictionCreate, connection: Optional[Connection] = None
    ) -> None:
        table = Table(self.tablename)
        sql = PostgreSQLQuery.into(table).columns(
            "enrollment_id", "module_id", "created_by"
        )

        for module_id in cmd.module_ids:
            sql = sql.insert(cmd.enrollment_id, module_id, cmd.created_by)
        sql = sql.get_sql()

        executable = ExecutableSQL(sql=sql, values=tuple())

        await self.db.execute(executable, fetch_returns="none", connection=connection)

    async def delete(
        self, cmd: ModuleRestrictionDelete, connection: Optional[Connection] = None
    ) -> None:
        table = Table(self.tablename)
        sql = (
            PostgreSQLQuery.from_(table)
            .where(
                Criterion.all(
                    terms=[
                        table.enrollment_id == Parameter("$1"),
                        table.module_id == Parameter("ANY($2::int[])"),
                    ]
                )
            )
            .delete()
            .get_sql()
        )

        executable = ExecutableSQL(sql=sql, values=(cmd.enrollment_id, cmd.module_ids))

        await self.db.execute(executable, fetch_returns="none", connection=connection)

    async def get_module_restrictions(
        self, enrollment_id: int, connection: Optional[Connection] = None
    ) -> set[int]:
        table = Table(self.tablename)
        sql = (
            PostgreSQLQuery.from_(table)
            .where(table.enrollment_id == Parameter("$1"))
            .select("module_id")
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(enrollment_id,))

        result = await self.db.execute(
            executable, fetch_returns="all", connection=connection
        )

        return {module_id["module_id"] for module_id in result}
