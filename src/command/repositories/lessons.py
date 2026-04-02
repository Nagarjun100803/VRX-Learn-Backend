from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel

from src.command.commands.lessons import (
    Lesson,
    LessonCreateWithPosition,
    LessonDelete,
    LessonGet,
    LessonUpdate,
)
from src.command.repositories.base import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    tablename: ClassVar[str] = "lessons"

    def _to_domain(self, row: Optional[Record]) -> Optional[Lesson]:
        if row is None:
            return None
        return Lesson.model_validate(dict(row))

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Lesson:
        cmd = self._normalize(cmd, LessonCreateWithPosition)
        return await super().add(cmd, connection=connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:
        cmd = self._normalize(cmd, LessonUpdate)
        return await super().update(cmd, connection=connection)

    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:

        cmd = self._normalize(cmd, LessonDelete)
        return await super().delete(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:
        query = self._normalize(query, LessonGet)
        return await super().get(query, connection=connection)
