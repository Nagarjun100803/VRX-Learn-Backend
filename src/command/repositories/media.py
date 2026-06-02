from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Criterion, Parameter, Table
from pypika.dialects import PostgreSQLQuery

from src.command.commands.media import (
    Media,
    MediableType,
    MediaCreate,
    MediaDelete,
    MediaGet,
    MediaStatusUpdate,
)
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL


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

    async def get_by_mediable(
        self,
        mediable_id: int,
        mediable_type: MediableType,
        connection: Optional[Connection] = None,
    ) -> Optional[Media]:

        table = Table(self.tablename)
        sql = (
            PostgreSQLQuery()
            .from_(table)
            .where(
                Criterion.all(
                    terms=[
                        table.mediable_id == Parameter("$1"),
                        table.mediable_type == Parameter("$2"),
                        table.deleted_at.isnull(),
                    ]
                )
            )
            .select("*")
        ).get_sql()

        executable = ExecutableSQL(sql, values=(mediable_id, mediable_type))

        return self._to_domain(
            await self.db.execute(
                executable, fetch_returns="one", connection=connection
            )
        )
