from asyncpg import Connection, Record
from typing import Optional, ClassVar
from src.command.repositories.base import BaseRepository
from src.command.commands.media import MediaCreate, MediaGet, MediaStatusUpdate, MediaDelete, Media


class MediaRepository(BaseRepository[Media]):
    
    tablename: ClassVar[str] = "media_assets"

    def _to_domain(self, row: Optional[Record]) -> Optional[Media]:
        if row is None:
            return None
        return Media(**row)

    
    async def add(self, cmd: MediaCreate, connection: Optional[Connection] = None) -> Media:
        return await super().add(cmd, connection=connection)
    
    async def update(self, cmd: MediaStatusUpdate, connection: Optional[Connection] = None) -> Optional[Media]:
        return await super().update(cmd, connection=connection)
    
    async def delete(self, cmd: MediaDelete, connection: Optional[Connection] = None) -> Optional[Media]:
        return await super().delete(cmd, connection=connection)
    
    async def get(self, query: MediaGet, connection: Optional[Connection] = None) -> Optional[Media]:
        return await super().get(query, connection=connection)
