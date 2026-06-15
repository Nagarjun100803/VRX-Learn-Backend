from typing import ClassVar, Type
from uuid import uuid4

from src.auth import Entity
from src.command.commands.base import AttachmentUploadContext, MediaContext
from src.command.commands.issues import (
    Issue,
    IssueAttachmentMetadata,
    IssueAttachmentStatusUpdate,
    IssueContext,
    IssueCreate,
    IssueGet,
    IssueStatusUpdate,
)
from src.command.commands.media import (
    MediableType,
    MediaCreate,
    MediaStatusUpdateByMediable,
)
from src.command.repositories import IssueRepository
from src.command.services.base import BaseService
from src.command.services.media import AttachmentResolver, MediaService
from src.core.storage import FileMetadata, S3Bucket
from src.exceptions import EntityNotFoundError, IssueNotFoundError


class IssueService(BaseService[Issue]):
    _entity: ClassVar[Entity] = Entity.ISSUE
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = IssueNotFoundError

    def __init__(
        self,
        repo: IssueRepository,
        media_service: MediaService,
        file_service: S3Bucket,
        attachment_resolver: AttachmentResolver,
    ) -> None:
        self.repo = repo
        self.media_service = media_service
        self.file_service = file_service
        self.attachment_resolver = attachment_resolver

    async def create(self, cmd: IssueCreate) -> Issue:
        return await self.repo.add(cmd)

    def _generate_storage_key(self, filename: str) -> str:
        return f"issues-attachment/{str(uuid4())}/{filename}"

    def _prepare_media_create_payload(
        self, issue_id: int, cmd: IssueCreate, attachment: IssueAttachmentMetadata
    ) -> MediaCreate:

        key = self._generate_storage_key(filename=attachment.filename)
        return MediaCreate(
            filename=attachment.filename,
            mime_type=attachment.content_type,
            file_size=attachment.size,
            mediable_id=issue_id,
            mediable_type=MediableType.ISSUE,
            key=key,
            created_by=cmd.created_by,
        )

    async def create_with_attachment(
        self, cmd: IssueCreate, attachment: IssueAttachmentMetadata
    ) -> AttachmentUploadContext[IssueContext]:

        async with self.repo.db.transaction() as tconn:
            issue = await self.repo.add(cmd, connection=tconn)
            media_cmd = self._prepare_media_create_payload(
                issue_id=issue.id, cmd=cmd, attachment=attachment
            )
            media = await self.media_service.create(cmd=media_cmd, connection=tconn)

        url = await self.file_service.get_upload_url(
            metadata=FileMetadata(
                key=media.key, content_type=media.mime_type, filename=media.filename
            )
        )

        return AttachmentUploadContext[IssueContext](
            data=IssueContext(**issue.model_dump()),
            media=MediaContext(
                id=media.id,
                url=url,
                filename=media.filename,
                content_type=media.mime_type,
                size=media.file_size,
            ),
        )

    async def update(self, cmd: IssueStatusUpdate) -> Issue:
        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    async def get(self, query: IssueGet) -> Issue:
        return self._require_entity(await self.repo.get(query), value=query.id)

    async def mark_attachment_as_uploaded(
        self, cmd: IssueAttachmentStatusUpdate
    ) -> None:
        await self.media_service.update(
            cmd=MediaStatusUpdateByMediable(
                mediable_id=cmd.id,
                mediable_type=MediableType.ISSUE,
                updated_by=cmd.updated_by,
            )
        )

    async def get_attachment_view_url(self, query: IssueGet) -> str:
        return await self.attachment_resolver.get_attachment_url(
            mediable_id=query.id, mediable_type=MediableType.ISSUE
        )
