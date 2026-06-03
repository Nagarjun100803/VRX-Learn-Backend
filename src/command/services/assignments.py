import asyncio
from typing import ClassVar, Type
from uuid import uuid4

from slugify import slugify

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.assignments import (
    Assignment,
    AssignmentAttachmentMetadata,
    AssignmentAttachmentStatusUpdate,
    AssignmentAttachmentUploadContext,
    AssignmentCreate,
    AssignmentDelete,
    AssignmentGet,
    AssignmentGetQuery,
    AssignmentUpdate,
)
from src.command.commands.media import (
    MediableType,
    MediaCreate,
    MediaStatusUpdateByMediable,
)
from src.command.repositories import AssignmentRepository, CourseRepository
from src.command.services.base import BaseService
from src.command.services.media import AttachmentResolver, MediaService
from src.core.storage.files import FileMetadata, S3Bucket
from src.exceptions import (
    AssignmentAlreadyExistsError,
    AssignmentNotFoundError,
    CourseNotFoundError,
    EntityNotFoundError,
)


class AssignmentService(BaseService[Assignment]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = AssignmentNotFoundError
    _entity: ClassVar[Entity] = Entity.ASSIGNMENT

    def __init__(
        self,
        repo: AssignmentRepository,
        course_repo: CourseRepository,
        media_service: MediaService,
        auth_service: AuthService,
        file_service: S3Bucket,
        attachment_resolver: AttachmentResolver,
    ) -> None:
        self.repo = repo
        self.course_repo = course_repo
        self.media_service = media_service
        self.auth_service = auth_service
        self.file_service = file_service
        self.attachment_resolver = attachment_resolver

    async def _validate_title(self, title: str, course_id: int) -> None:
        if await self.repo.exists_by(title=title, course_id=course_id):
            raise AssignmentAlreadyExistsError(value=title, identifier="title")

    async def _validate_assignment_create(self, cmd: AssignmentCreate) -> None:
        course_exists, _ = await asyncio.gather(
            self.course_repo.exists_by(id=cmd.course_id),
            self._validate_title(title=cmd.title, course_id=cmd.course_id),
        )
        if not course_exists:
            raise CourseNotFoundError(value=cmd.course_id, identifier="course_id")
        # Later can add more validation here.

    def _generate_storage_key(self, filename: str, course_id: int) -> str:
        slugged_filename = slugify(filename)
        return f"courses/C-{course_id}/assignments/{str(uuid4())}/{slugged_filename}"

    def _prepare_media_create_payload(
        self,
        assignment_id: int,
        cmd: AssignmentCreate,
        attachment: AssignmentAttachmentMetadata,
    ) -> MediaCreate:
        key = self._generate_storage_key(
            filename=attachment.filename, course_id=cmd.course_id
        )
        return MediaCreate(
            filename=attachment.filename,
            mime_type=attachment.content_type,
            file_size=attachment.size,
            mediable_id=assignment_id,
            mediable_type=MediableType.ASSIGNMENT,
            key=key,
            created_by=cmd.created_by,
        )

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.ASSIGNMENT,
        user_id_field="created_by",
        entity_id_field=None,
        parent_id_field="course_id",
    )
    async def create(self, cmd: AssignmentCreate) -> Assignment:
        await self._validate_assignment_create(cmd=cmd)
        return await self.repo.add(cmd=cmd)

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.ASSIGNMENT,
        user_id_field="created_by",
        entity_id_field=None,
        parent_id_field="course_id",
    )
    async def create_with_attachment(
        self, cmd: AssignmentCreate, attachment: AssignmentAttachmentMetadata
    ) -> AssignmentAttachmentUploadContext:

        await self._validate_assignment_create(cmd=cmd)

        async with self.repo.db.transaction() as tconn:
            assignment = await self.repo.add(cmd=cmd, connection=tconn)
            media_cmd = self._prepare_media_create_payload(
                assignment_id=assignment.id, cmd=cmd, attachment=attachment
            )
            media = await self.media_service.create(cmd=media_cmd, connection=tconn)

        url = await self.file_service.get_upload_url(
            metadata=FileMetadata(
                key=media.key, filename=media.filename, content_type=media.mime_type
            )
        )
        return AssignmentAttachmentUploadContext(
            **assignment.model_dump(), media_id=media.id, url=url
        )

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.ASSIGNMENT,
        user_id_field="updated_by",
        entity_id_field="id",
    )
    async def update(self, cmd: AssignmentUpdate) -> Assignment:
        assignment = await self.repo.get(query=AssignmentGet(id=cmd.id))
        if assignment is None:
            raise AssignmentNotFoundError(value=cmd.id)

        if assignment.title != cmd.title:
            await self._validate_title(
                title=str(cmd.title), course_id=assignment.course_id
            )

        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    @require_authorization(
        action=Action.DELETE,
        entity=Entity.ASSIGNMENT,
        user_id_field="deleted_by",
        entity_id_field="id",
    )
    async def delete(self, cmd: AssignmentDelete):
        return self._require_entity(await self.repo.delete(cmd), value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: AssignmentGetQuery):
        return self._require_entity(
            await self.repo.get(AssignmentGet(id=query.id)), value=query.id
        )

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.ASSIGNMENT,
        user_id_field="updated_by",
        entity_id_field="id",
    )
    async def mark_attachment_as_uploaded(
        self, cmd: AssignmentAttachmentStatusUpdate
    ) -> None:
        await self.media_service.update(
            cmd=MediaStatusUpdateByMediable(
                mediable_id=cmd.id,
                mediable_type=MediableType.ASSIGNMENT,
                updated_by=cmd.updated_by,
            )
        )

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get_attachment_view_url(self, query: AssignmentGetQuery) -> str:
        return await self.attachment_resolver.get_attachment_url(
            mediable_id=query.id, mediable_type=MediableType.ASSIGNMENT
        )
