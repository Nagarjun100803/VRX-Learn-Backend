import asyncio
from typing import ClassVar, Type, cast

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.modules import (
    Module,
    ModuleCreate,
    ModuleCreateWithPosition,
    ModuleDelete,
    ModuleGetQuery,
    ModuleReorderParticipants,
    ModuleUpdate,
)
from src.command.repositories.courses import CourseRepository
from src.command.repositories.modules import ModuleRepository
from src.command.services.base import BaseService
from src.command.services.positioning import PositioningService, ReorderParticipants
from src.events.events import ModuleCreatedEvent, ModuleDeletedEvent
from src.events.publishers import module_created_publisher, module_deleted_publisher
from src.exceptions import (
    CourseModuleAlreadyExistsError,
    CourseModuleNotFoundError,
    CourseNotFoundError,
    EntityNotFoundError,
)


class ModuleService(BaseService[Module]):
    _entity: ClassVar[Entity] = Entity.MODULE
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseModuleNotFoundError

    def __init__(
        self,
        repo: ModuleRepository,
        course_repo: CourseRepository,
        auth_service: AuthService,
        positioning_service: PositioningService,
    ) -> None:

        self.repo = repo
        self.course_repo = course_repo
        self.auth_service = auth_service
        self.positioning_service = positioning_service

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.MODULE,
        user_id_field="created_by",
        parent_id_field="course_id",
        object_name="cmd",
    )
    async def create(self, cmd: ModuleCreate) -> Module:

        # Conditions
        course_exist_flag, duplicate_module_title_flag = await asyncio.gather(
            self.course_repo.exists_by(id=cmd.course_id),
            self.repo.exists_by(title=cmd.title, course_id=cmd.course_id),
        )
        # Check for course existance.
        if not course_exist_flag:
            raise CourseNotFoundError(value=cmd.course_id)

        # Check for duplicate module name in a course.
        if duplicate_module_title_flag:
            raise CourseModuleAlreadyExistsError(cmd.title, identifier="title")

        position_string = await self.positioning_service.generate_position(
            tablename=self.repo.tablename, scope="course_id", scope_id=cmd.course_id
        )

        module = await self.repo.add(
            ModuleCreateWithPosition(
                **cmd.model_dump(), position_string=position_string
            )
        )

        if module is not None:
            # Publish the module created event.
            await module_created_publisher.publish(
                ModuleCreatedEvent(
                    id=module.id,
                    created_by=module.created_by,  # type: ignore
                    course_id=module.course_id,
                )
            )

        return cast(Module, module)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.MODULE,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def update(self, cmd: ModuleUpdate) -> Module:
        # Get the module.
        module = await self.repo.pick(
            columns=["id", "title", "course_id"], fetch_all=False, id=cmd.id
        )
        if module is None:
            raise CourseModuleNotFoundError(value=cmd.id)

        # Check for title change.
        if cmd.title != dict(module)["title"]:
            duplicate_title_flag = await self.repo.exists_by(
                title=cmd.title, course_id=dict(module)["course_id"]
            )
            if duplicate_title_flag:
                raise CourseModuleAlreadyExistsError(
                    value=cmd.title, identifier="title"
                )

        # Update the fields.
        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    @require_authorization(
        action=Action.DELETE,
        entity=Entity.MODULE,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def delete(self, cmd: ModuleDelete) -> Module:
        module = await self.repo.delete(cmd)

        if module is not None:
            # Publish the module deleted event.
            await module_deleted_publisher.publish(
                ModuleDeletedEvent(
                    id=module.id,
                    course_id=module.course_id,
                    deleted_by=module.deleted_by,  # type: ignore
                )
            )

        return self._require_entity(module, value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.MODULE,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: ModuleGetQuery) -> Module:
        module = await self.repo.get(query)
        return self._require_entity(module, value=query.id)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.MODULE,
        user_id_field="updated_by",
        entity_id_field="target_id",
    )
    async def reorder(self, cmd: ModuleReorderParticipants) -> str:
        return await self.positioning_service.reorder(
            participants=ReorderParticipants(
                preceding_id=cmd.preceding_id,
                target_id=cmd.target_id,
                succeeding_id=cmd.succeeding_id,
            ),
            tablename="modules",
            scope="course_id",
        )
