from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel

from src.command.commands.media import (
    Media,
    MediaCreate,
    MediaDelete,
    MediaGet,
    MediaStatusUpdate,
)
from src.command.repositories.base import BaseRepository


class MediaRepository(BaseRepository[Media]):
    tablename: ClassVar[str] = "media_assets"

    def _to_domain(self, row: Optional[Record]) -> Optional[Media]:
        if row is None:
            return None
        return Media.model_validate(dict(row))

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Media:
        cmd = self._normalize(cmd, MediaCreate)
        return await super().add(cmd, connection=connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Media]:
        cmd = self._normalize(cmd, MediaStatusUpdate)
        return await super().update(cmd, connection=connection)

    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Media]:
        cmd = self._normalize(cmd, MediaDelete)
        return await super().delete(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Media]:
        query = self._normalize(query, MediaGet)
        return await super().get(query, connection=connection)
