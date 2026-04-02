from typing import ClassVar, Optional, override

from asyncpg import Connection, Record
from pydantic import BaseModel

from src.command.commands.modules import (
    Module,
    ModuleCreateWithPosition,
    ModuleDelete,
    ModuleGet,
    ModuleUpdate,
)
from src.command.repositories.base import BaseRepository


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

    @override
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Module]:
        # Unlink the relationships.
        cmd = self._normalize(cmd, ModuleDelete)
        return await super().delete(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Module]:
        query = self._normalize(query, ModuleGet)
        return await super().get(query, connection=connection)
