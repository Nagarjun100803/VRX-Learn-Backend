import asyncio
from typing import ClassVar, Optional, Type, cast
from uuid import uuid4

from asyncpg import Connection
from slugify import slugify

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.lessons import (
    Lesson,
    LessonCreate,
    LessonCreateWithPosition,
    LessonDelete,
    LessonGetQuery,
    LessonReorderParticipants,
    LessonUpdate,
    LessonUploadUrl,
)
from src.command.commands.media import MediableType, MediaCreate, MediaStatus
from src.command.commands.modules import Module, ModuleGet
from src.command.repositories.lessons import LessonRepository
from src.command.repositories.modules import ModuleRepository
from src.command.services.base import BaseService
from src.command.services.files import FileMetadata
from src.command.services.media import MediaService
from src.command.services.positioning import PositioningService, ReorderParticipants
from src.events.events import (
    LessonCreatedEvent,
    LessonDeletedEvent,
    LessonReorderedEvent,
    LessonUpdatedEvent,
)
from src.events.publishers import (
    lesson_created_publisher,
    lesson_deleted_publisher,
    lesson_reordered_publisher,
    lesson_updated_publisher,
)
from src.exceptions import (
    CourseModuleNotFoundError,
    EntityNotFoundError,
    LessonAlreadyExistsError,
    LessonNotFoundError,
)


class LessonService(BaseService[Lesson]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = LessonNotFoundError
    _entity: ClassVar[Entity] = Entity.LESSON

    def __init__(
        self,
        repo: LessonRepository,
        module_repo: ModuleRepository,
        media_service: MediaService,
        auth_service: AuthService,
        positioning_service: PositioningService,
    ) -> None:

        self.repo = repo
        self.module_repo = module_repo
        self.media_service = media_service
        self.auth_service = auth_service
        self.positioning_service = positioning_service

    async def _validate_module(self, module_id: int) -> Module:

        module = await self.module_repo.get(ModuleGet(id=module_id))

        if module is None:
            raise CourseModuleNotFoundError(value=module_id)

        return module

    async def _check_duplicate_lesson_title(self, title: str, module_id: int) -> None:

        duplicate_title_flag = await self.repo.exists_by(
            title=title, module_id=module_id
        )

        if duplicate_title_flag:
            raise LessonAlreadyExistsError(value=title, identifier="title")

        return None

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.LESSON,
        user_id_field="created_by",
        parent_id_field="module_id",
        object_name="cmd",
    )
    async def create(
        self, cmd: LessonCreate, connection: Optional[Connection] = None
    ) -> Lesson:

        position_string = await self.positioning_service.generate_position(
            tablename=self.repo.tablename, scope="module_id", scope_id=cmd.module_id
        )

        lesson = await self.repo.add(
            LessonCreateWithPosition(
                **cmd.model_dump(), position_string=position_string
            ),
            connection=connection,
        )

        await lesson_created_publisher.publish(
            LessonCreatedEvent(
                id=lesson.id,
                module_id=lesson.module_id,
                created_by=lesson.created_by,  # type: ignore
            )
        )

        return cast(Lesson, lesson)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.LESSON,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd",
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

        lesson = await self.repo.update(cmd)
        # Publish lesson updated event.
        if lesson is not None:
            await lesson_updated_publisher.publish(
                LessonUpdatedEvent(
                    id=lesson.id,
                    module_id=lesson.module_id,
                    updated_by=lesson.updated_by,  # type: ignore
                )
            )

        return self._require_entity(lesson, value=cmd.id)

    @require_authorization(
        action=Action.DELETE,
        entity=Entity.LESSON,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def delete(self, cmd: LessonDelete) -> Lesson:
        # TODO: Need to delete the actual file from the object storage also.

        lesson = await self.repo.delete(cmd)

        if lesson is not None:
            await lesson_deleted_publisher.publish(
                LessonDeletedEvent(
                    id=lesson.id,
                    module_id=lesson.module_id,
                    deleted_by=lesson.deleted_by,  # type: ignore
                )
            )

        return self._require_entity(lesson, value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.LESSON,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: LessonGetQuery):
        return self._require_entity(await self.repo.get(query), value=query.id)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.LESSON,
        user_id_field="updated_by",
        entity_id_field="target_id",
        object_name="cmd",
    )
    async def reorder(self, cmd: LessonReorderParticipants) -> str:
        position_string = await self.positioning_service.reorder(
            participants=ReorderParticipants(
                preceding_id=cmd.preceding_id,
                target_id=cmd.target_id,
                succeeding_id=cmd.succeeding_id,
            ),
            tablename="lessons",
            scope="module_id",
        )
        await lesson_reordered_publisher.publish(
            LessonReorderedEvent(
                id=cmd.target_id,
                updated_by=cmd.updated_by,  # type: ignore
            )
        )
        return position_string

    async def init_lesson_create(
        self, cmd: LessonCreate, file_cmd: FileMetadata
    ) -> LessonUploadUrl:

        async with self.repo.db.transaction() as connection:
            module, _ = await asyncio.gather(
                self._validate_module(module_id=cmd.module_id),
                self._check_duplicate_lesson_title(
                    title=cmd.title, module_id=cmd.module_id
                ),
            )

            lesson = await self.create(cmd, connection=connection)

            slugged_filename = slugify(file_cmd.filename)

            key = f"courses/C-{module.course_id}/modules/{module.id}/lessons/{str(uuid4())}/{slugged_filename}"

            media = MediaCreate(
                filename=file_cmd.filename,
                mime_type=file_cmd.content_type,
                file_size=file_cmd.size,
                mediable_id=lesson.id,
                mediable_type=MediableType.LESSON,
                created_by=lesson.created_by,  # type: ignore[arg-type]
                is_private=True,
                status=MediaStatus.PENDING,
                key=key,
            )

            media_id, upload_url = await self.media_service.prepare_upload_url(
                media, expire_mins=120, connection=connection
            )

        return LessonUploadUrl(
            media_id=media_id, lesson_id=lesson.id, upload_url=upload_url
        )
