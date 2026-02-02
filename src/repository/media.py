from asyncpg.protocol.record import Record
from typing import Optional, Union,  ClassVar
from src.repository.base import BaseRepository
from src.commands.media import MediaCreate, MediaGet, MediaStatusUpdate, MediaDelete, Media



class MediaRepository(BaseRepository[Media]):
    
    tablename: ClassVar[str] = "media_assets"
    _ownership_spec = None 

    def _to_domain(self, row: Optional[Record]) -> Optional[Media]:
        if row is None:
            return None
        return Media(**row)

    
    async def add(self, cmd: MediaCreate) -> Media:
        return await super().add(cmd)
    
    async def update(self, cmd: MediaStatusUpdate) -> Optional[Media]:
        return await super().update(cmd)
    
    async def delete(self, cmd: MediaDelete) -> Optional[Media]:
        return await super().delete(cmd)
    
    async def get(self, query: MediaGet) -> Optional[Media]:
        return await super().get(query)
