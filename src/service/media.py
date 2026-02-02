"""     
    This is responsible for creating the media records in the database
    and generating presigned urls for upload and view.
    This orchestrates between the file storage service and the media repository.
    
"""

from typing import Optional
from dataclasses import dataclass
from src.service.files import S3, FileMetadata
from src.repository.media import MediaRepository
from src.commands.media import Media, MediaCreate, MediaStatusUpdate, MediaDelete, MediaGet
from src.exceptions import MediaNotFoundError, MediaAlreadyExistsError

# NOTE: Media Assests table allows more than one file for a mediable_type, Eg. LESSON, ASSIGNMENT etc.

@dataclass
class MediaService:
    file_service: S3
    repo: MediaRepository
    
    
    def _require_entity(self, entity: Optional[Media], **error_kwargs) -> Media:
        if entity is None:
            raise MediaNotFoundError(**error_kwargs)
        return entity

    
    async def create(self, cmd: MediaCreate) -> Media:
        if await self.repo.exists_by(filename=cmd.filename):
            raise MediaAlreadyExistsError(cmd.filename, identifier="filename/key")
        return await self.repo.add(cmd)
        

    async def update(self, cmd: MediaStatusUpdate) -> Media:
        return self._require_entity(
            await self.repo.update(cmd)
        )
    
    async def delete(self, cmd: MediaDelete) -> Media:
        return self._require_entity(
            await self.repo.delete(cmd)
        )
    
    
    async def get(self, query: MediaGet) -> Media:
        return self._require_entity(
            await self.repo.get(query)
        )
    
    
    async def prepare_upload_url(self, cmd: MediaCreate, expire_mins: int = 120) -> str:
        # Create a table record with a pending.
        media = await self.create(cmd)
        # Generate presigned url for upload/
        return await self.file_service.generate_presigned_url(
            file_metadata=FileMetadata(
                filename=media.filename,
                content_type=media.mime_type,
                size=media.file_size
            ),
            expire_mins=expire_mins
        )
    
    async def get_view_url(self, media_id: int, expire_mins: int = 60) -> str:
        media = self._require_entity(
            await self.repo.get(
                MediaGet(id=media_id)
            ),
            value=media_id
        )
        return await self.file_service.get_presigned_url(
            media.filename,
            expire_mins=expire_mins
        )
   

    


