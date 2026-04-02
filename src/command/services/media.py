"""
This is responsible for creating the media records in the database
and generating presigned urls for upload and view.
This orchestrates between the file storage service and the media repository.

"""

from dataclasses import dataclass
from typing import Optional, cast

from asyncpg import Connection

from src.command.commands.media import (
    Media,
    MediaCreate,
    MediaDelete,
    MediaGet,
    MediaStatusUpdate,
)
from src.command.repositories.media import MediaRepository
from src.command.services.files import S3, StorageMetadata
from src.exceptions import MediaAlreadyExistsError, MediaNotFoundError

# NOTE: Media Assests table allows more than one file for a mediable_type, Eg. LESSON, ASSIGNMENT etc.


@dataclass(slots=True, kw_only=True)
class MediaService:
    """
    Workflow for uploading a media file:
    1. Client requests for an upload url with the file metadata (filename, size, content type etc.)
    2. We create a record in the media_assets table with status as pending.
    3. We generate a presigned url for upload and return to the client.
    4. Client uploads the file to the object storage using the presigned url.
    5. Once the file is uploaded, client calls an endpoint to update the status of the media record to UPLOADED.

    Here all service methods accepts an optional connection parameter. This is to allow the caller to manage the transaction if needed.
    If the connection is not provided, the service will use its own connection from the connection pool.
    This is useful in scenarios where the media record creation needs to be part of a larger transaction, for example when creating a lesson along with its media record. In such cases,
    we want both the lesson and media record creation to be atomic.

    NOTE: This is a core service that can be used by multiple other services like LessonService, AssignmentService etc. That's why we allow the caller to manage the transaction.
    For example, when creating a lesson along with its media record, we want both the lesson and media record creation to be atomic.
    So the LessonService can create a transaction, call the MediaService to create the media record and then generate a signed url. If any of the operations fail,
    the entire transaction can be rolled back to maintain data integrity.
    """

    file_service: S3
    repo: MediaRepository

    def _require_entity(self, entity: Optional[Media], **error_kwargs) -> Media:
        if entity is None:
            raise MediaNotFoundError(**error_kwargs)
        return entity

    async def create(
        self, cmd: MediaCreate, connection: Optional[Connection] = None
    ) -> Media:
        if await self.repo.exists_by(key=cmd.key):
            raise MediaAlreadyExistsError(cmd.key, identifier="key")
        return cast(Media, await self.repo.add(cmd, connection=connection))

    # NOTE: No Authorization logic implemented.
    async def update(
        self, cmd: MediaStatusUpdate, connection: Optional[Connection] = None
    ) -> Media:
        return self._require_entity(
            await self.repo.update(cmd, connection=connection), value=cmd.id
        )

    async def delete(
        self, cmd: MediaDelete, connection: Optional[Connection] = None
    ) -> Media:
        return self._require_entity(
            await self.repo.delete(cmd, connection=connection), value=cmd.id
        )

    async def get(
        self, query: MediaGet, connection: Optional[Connection] = None
    ) -> Media:
        return self._require_entity(
            await self.repo.get(query, connection=connection), value=query.id
        )

    async def prepare_upload_url(
        self,
        cmd: MediaCreate,
        expire_mins: int = 120,
        connection: Optional[Connection] = None,
    ) -> tuple[int, str]:
        # Create a table record with a pending.
        media = await self.create(cmd, connection=connection)

        # Generate presigned url for upload/
        file_metadata = StorageMetadata(
            key=cmd.key, content_type=media.mime_type, size=media.file_size
        )

        url = await self.file_service.generate_presigned_url(
            file_metadata=file_metadata, expire_mins=expire_mins
        )

        return (media.id, url)

    async def get_view_url(
        self,
        media_id: int,
        expire_mins: int = 60,
        connection: Optional[Connection] = None,
    ) -> str:

        media = self._require_entity(
            await self.repo.get(MediaGet(id=media_id), connection=connection),
            value=media_id,
        )
        return await self.file_service.get_presigned_url(
            media.key,
            expire_mins=expire_mins,
            filename=media.filename,
            mime_type=media.mime_type,
        )
