import asyncio
from typing import ClassVar, Type
from uuid import uuid4

from src.auth import Entity
from src.command.commands.base import AttachmentUploadContext, MediaContext
from src.command.commands.lessons import (
    AllowedLessonAttachmentContentTypes,
    Lesson,
    LessonAttachmentMetadata,
    LessonAttachmentStatusUpdate,
    LessonContext,
    LessonCreate,
    LessonCreateWithPosition,
    LessonDelete,
    LessonGetQuery,
    LessonReorderParticipants,
    LessonUpdate,
    LessonWithMedia,
)
from src.command.commands.media import (
    MediableType,
    MediaCreate,
    MediaStatusUpdateByMediable,
)
from src.command.repositories import LessonRepository, ModuleRepository
from src.command.services.base import BaseService
from src.command.services.media import AttachmentResolver, MediaService
from src.command.services.module_restrictions import ModuleAccessService
from src.core.positioning import PositioningService, ReorderParticipants
from src.core.storage import FileMetadata, S3Bucket
from src.exceptions import (
    CourseModuleNotFoundError,
    EntityNotFoundError,
    LessonAlreadyExistsError,
    LessonNotFoundError,
    ValidationError,
)


class LessonService(BaseService[Lesson]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = LessonNotFoundError
    _entity: ClassVar[Entity] = Entity.LESSON

    def __init__(
        self,
        repo: LessonRepository,
        module_repo: ModuleRepository,
        media_service: MediaService,
        file_service: S3Bucket,
        positioning_service: PositioningService,
        attachment_resolver: AttachmentResolver,
        module_access_service: ModuleAccessService,
    ) -> None:
        self.repo = repo
        self.module_repo = module_repo
        self.media_service = media_service
        self.file_service = file_service
        self.positioning_service = positioning_service
        self.attachment_resolver = attachment_resolver
        self.module_access_service = module_access_service

    async def _check_duplicate_lesson_title(self, title: str, module_id: int) -> None:
        duplicate_title_flag = await self.repo.exists_by(
            title=title, module_id=module_id
        )
        if duplicate_title_flag:
            raise LessonAlreadyExistsError(value=title, identifier="title")

    async def _validate_lesson_create(
        self, cmd: LessonCreate, attachment: LessonAttachmentMetadata
    ) -> None:

        if (
            attachment.content_type != AllowedLessonAttachmentContentTypes.MP4
            and cmd.is_preview
        ):
            raise ValidationError("Preview lessons must have an MP4 attachment.")

        module_exists, _ = await asyncio.gather(
            self.module_repo.exists_by(id=cmd.module_id),
            self._check_duplicate_lesson_title(
                title=cmd.title, module_id=cmd.module_id
            ),
        )
        if not module_exists:
            raise CourseModuleNotFoundError(value=cmd.module_id)

    async def _generate_storage_key(self, filename: str, module_id: int) -> str:
        # Pick course id from the module id.
        course_id = await self.module_repo.pick(
            columns=["course_id"], fetch_all=False, id=module_id
        )
        if course_id is None:
            raise CourseModuleNotFoundError(value=module_id)

        course_id = dict(course_id)["course_id"]

        return f"courses/C-{course_id}/modules/M-{module_id}/lessons/{str(uuid4())}/{filename}"

    async def _prepare_media_create_payload(
        self, lesson_id: int, cmd: LessonCreate, attachment: LessonAttachmentMetadata
    ):
        key = await self._generate_storage_key(
            filename=attachment.filename, module_id=cmd.module_id
        )
        return MediaCreate(
            filename=attachment.filename,
            mime_type=attachment.content_type,
            file_size=attachment.size,
            mediable_id=lesson_id,
            mediable_type=MediableType.LESSON,
            key=key,
            created_by=cmd.created_by,
        )

    async def create(
        self, cmd: LessonCreate, attachment: LessonAttachmentMetadata
    ) -> AttachmentUploadContext[LessonContext]:

        await self._validate_lesson_create(cmd, attachment)

        position_string = await self.positioning_service.generate_position(
            tablename=self.repo.tablename, scope="module_id", scope_id=cmd.module_id
        )

        async with self.repo.db.transaction() as tconn:
            lesson = await self.repo.add(
                cmd=LessonCreateWithPosition(
                    **cmd.model_dump(), position_string=position_string
                ),
                connection=tconn,
            )
            media_cmd = await self._prepare_media_create_payload(
                lesson.id, cmd, attachment
            )
            media = await self.media_service.create(cmd=media_cmd, connection=tconn)

        url = await self.file_service.get_upload_url(
            metadata=FileMetadata(
                key=media.key,
                content_type=media.mime_type,
                filename=attachment.filename,
            )
        )
        return AttachmentUploadContext[LessonContext](
            data=LessonContext(**lesson.model_dump()),
            media=MediaContext(
                id=media.id,
                filename=attachment.filename,
                content_type=media.mime_type,
                size=attachment.size,
                url=url,
            ),
        )

    async def update(self, cmd: LessonUpdate) -> Lesson:

        lesson = await self.repo.pick(
            columns=("id", "module_id"), fetch_all=False, id=cmd.id
        )
        if not lesson:
            raise LessonNotFoundError(value=cmd.id)

        # Check for duplicate title name in the same module.
        duplicate_lesson_title_flag = await self.repo.exists_by(
            title=cmd.title, module_id=lesson["module_id"]
        )
        if duplicate_lesson_title_flag:
            raise LessonAlreadyExistsError(value=cmd.title, identifier="title")

        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    async def delete(self, cmd: LessonDelete) -> Lesson:
        return self._require_entity(await self.repo.delete(cmd), value=cmd.id)

    async def get(self, query: LessonGetQuery) -> Lesson:
        return self._require_entity(await self.repo.get(query), value=query.id)

    async def get_with_media(self, query: LessonGetQuery) -> LessonWithMedia:
        result = await self.repo.get_with_media(query)
        if result is None:
            raise LessonNotFoundError(value=query.id)
        return result

    async def get_attachment_view_url(self, query: LessonGetQuery) -> str:
        lesson = await self.repo.pick(
            columns=["id", "module_id", "is_preview"], fetch_all=False, id=query.id
        )
        if lesson is None:
            raise LessonNotFoundError(value=query.id)

        # If the lesson is a preview, return the attachment URL immediately.
        if lesson["is_preview"]:
            return await self.attachment_resolver.get_attachment_url(
                mediable_id=query.id, mediable_type=MediableType.LESSON
            )

        # Otherwise, validate access and return the attachment URL.
        await self.module_access_service.validate_access(
            user_id=query.viewer_id, module_id=lesson["module_id"]
        )
        return await self.attachment_resolver.get_attachment_url(
            mediable_id=query.id, mediable_type=MediableType.LESSON
        )

    async def mark_attachment_as_uploaded(
        self, cmd: LessonAttachmentStatusUpdate
    ) -> None:
        await self.media_service.update(
            cmd=MediaStatusUpdateByMediable(
                mediable_id=cmd.id,
                mediable_type=MediableType.LESSON,
                updated_by=cmd.updated_by,
            )
        )

    async def reorder(self, cmd: LessonReorderParticipants) -> str:
        return await self.positioning_service.reorder(
            participants=ReorderParticipants(
                preceding_id=cmd.preceding_id,
                target_id=cmd.target_id,
                succeeding_id=cmd.succeeding_id,
            ),
            tablename="lessons",
            scope="module_id",
        )
