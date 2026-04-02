from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel

from src.command.commands.assignments import (
    Assignment,
    AssignmentCreate,
    AssignmentDelete,
    AssignmentGet,
    AssignmentUpdate,
)
from src.command.repositories.base import BaseRepository


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

    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Assignment]:
        # TODO: Need to unlink all the submitted assignments from it.
        cmd = self._normalize(cmd, AssignmentDelete)
        return await super().delete(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Assignment]:
        query = self._normalize(query, AssignmentGet)
        return await super().get(query, connection=connection)
