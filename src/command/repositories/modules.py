from typing import Any, ClassVar, Optional, override

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Criterion, Parameter, PostgreSQLQuery, functions

from src.command.commands.media import MediableType
from src.command.commands.modules import (
    Module,
    ModuleCreateWithPosition,
    ModuleDelete,
    ModuleGet,
    ModuleUpdate,
)
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.query_builder import lesson_table, media_asset_table, module_table


class ModuleRepository(BaseRepository[Module]):
    tablename: ClassVar[str] = "modules"

    @override
    def _to_domain(self, row: Optional[Record]):
        if row is None:
            return None
        return Module.model_validate(dict(row))

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Module:
        cmd = self._normalize(cmd, ModuleCreateWithPosition)
        return await super().add(cmd, connection=connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Module]:
        cmd = self._normalize(cmd, ModuleUpdate)
        return await super().update(cmd, connection=connection)

    async def _delete_lessons(
        self, cmd: ModuleDelete, connection: Optional[Connection] = None
    ) -> None:

        # Delete all the lessons associated with a module.
        lesson_ids_subquery = (
            PostgreSQLQuery.from_(lesson_table)
            .where(lesson_table.module_id == Parameter("$1"))
            .select(lesson_table.id)
        )

        delete_lesson_sql = (
            PostgreSQLQuery.update(lesson_table)
            .set(lesson_table.deleted_at, functions.Now())
            .set(lesson_table.deleted_by, Parameter("$2"))
            .where(lesson_table.module_id.isin(lesson_ids_subquery))
        ).get_sql()

        # Delete all the media associated with the lessons.
        delete_lesson_media_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_type == Parameter("$3"),
                        media_asset_table.mediable_id.isin(lesson_ids_subquery),
                    ]
                )
            )
        ).get_sql()

        executable1 = ExecutableSQL(
            sql=delete_lesson_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            sql=delete_lesson_media_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.LESSON),
        )

        await self.db.execute(executable1, fetch_returns="none", connection=connection)
        await self.db.execute(executable2, fetch_returns="none", connection=connection)

    async def _delete_module(
        self, cmd: ModuleDelete, connection: Optional[Connection] = None
    ) -> Optional[Module]:

        module_delete_query = (
            PostgreSQLQuery.update(module_table)
            .set(module_table.deleted_at, functions.Now())
            .set(module_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        module_table.deleted_at.isnull(),
                        module_table.id == Parameter("$1"),
                    ]
                )
            )
        )

        module_delete_query: Any = module_delete_query.returning("*")  # type: ignore
        module_delete_sql: str = module_delete_query.get_sql()

        executable = ExecutableSQL(
            sql=module_delete_sql, values=(cmd.id, cmd.deleted_by)
        )

        deleted_module = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return self._to_domain(deleted_module)

    @override
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Module]:

        cmd = self._normalize(cmd, ModuleDelete)
        async with self.db.transaction() as connection:
            await self._delete_lessons(cmd, connection=connection)
            return await self._delete_module(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Module]:
        query = self._normalize(query, ModuleGet)
        return await super().get(query, connection=connection)
