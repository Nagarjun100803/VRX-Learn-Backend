from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel

from src.command.commands.enrollments import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentDelete,
    EnrollmentGet,
    EnrollmentUpdate,
)
from src.command.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    tablename: ClassVar[str] = "enrollments"

    def _to_domain(self, row: Optional[Record]) -> Optional[Enrollment]:
        if row is None:
            return None
        return Enrollment.model_validate(dict(row))

    async def add(self, cmd: BaseModel, connection: Optional[Connection] = None):
        cmd = self._normalize(cmd, EnrollmentCreate)
        return await super().add(cmd, connection)

    async def update(self, cmd: BaseModel, connection: Optional[Connection] = None):
        cmd = self._normalize(cmd, EnrollmentUpdate)
        return await super().update(cmd, connection)

    async def delete(self, cmd: BaseModel, connection: Optional[Connection] = None):
        cmd = self._normalize(cmd, EnrollmentDelete)
        return await super().delete(cmd, connection)

    async def get(self, query: BaseModel, connection: Optional[Connection] = None):
        query = self._normalize(query, EnrollmentGet)
        return await super().get(query, connection)
