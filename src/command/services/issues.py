from typing import ClassVar, Optional, Type, Union
from uuid import uuid4

from asyncpg import Connection
from slugify import slugify

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.issues import (
    Issue,
    IssueCreate,
    IssueDetail,
    IssueGet,
    IssueStatusUpdate,
    IssueUpload,
)
from src.command.commands.media import MediableType, MediaCreate, MediaDetail
from src.command.repositories import IssueRepository
from src.command.services.base import BaseService
from src.command.services.files import FileMetadata
from src.command.services.media import MediaService
from src.exceptions import EntityNotFoundError, IssueNotFoundError


class IssueService(BaseService):
    def __init__(
        self,
        repo: IssueRepository,
        auth_service: AuthService,
        media_service: MediaService,
    ) -> None:

        self.repo = repo
        self.auth_service = auth_service
        self.media_service = media_service

    # Class Variables.
    _entity: ClassVar[Entity] = Entity.ISSUE
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = IssueNotFoundError

    async def _create(
        self, cmd: IssueCreate, connection: Optional[Connection] = None
    ) -> Issue:

        return await self.repo.add(cmd, connection=connection)

    async def _create_with_attachment(
        self, cmd: IssueCreate, file_cmd: FileMetadata
    ) -> IssueUpload:

        async with self.repo.db.transaction() as conn:
            issue = await self._create(cmd, connection=conn)

            # Generate a key for s3
            slugged_filname = slugify(file_cmd.filename)
            key = f"issues-attachment/{str(uuid4())}/{slugged_filname}"

            # Create media record.
            media_payload = MediaCreate(
                filename=slugged_filname,
                mime_type=file_cmd.content_type,
                file_size=file_cmd.size,
                mediable_id=issue.id,
                mediable_type=MediableType.ISSUE,
                key=key,
                created_by=cmd.created_by,
            )

            media_id, url = await self.media_service.prepare_upload_url(
                cmd=media_payload, connection=conn
            )

            return IssueUpload(
                issue=IssueDetail.model_validate(issue.model_dump()),
                media=MediaDetail(
                    media_id=media_id,
                    filename=slugged_filname,
                    upload_url=url,
                    mime_type=file_cmd.content_type,
                ),
            )

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.ISSUE,
        user_id_field="created_by",
        entity_id_field=None,
        parent_id_field=None,
    )
    async def create(
        self, cmd: IssueCreate, file_cmd: Optional[FileMetadata] = None
    ) -> Union[Issue, IssueUpload]:

        if file_cmd is None:
            return await self._create(cmd=cmd)

        return await self._create_with_attachment(cmd=cmd, file_cmd=file_cmd)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.ISSUE,
        user_id_field="updated_by",
        entity_id_field="id",
    )
    async def update(self, cmd: IssueStatusUpdate) -> Issue:
        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ISSUE,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: IssueGet) -> Issue:
        return self._require_entity(await self.repo.get(query), value=query.id)
