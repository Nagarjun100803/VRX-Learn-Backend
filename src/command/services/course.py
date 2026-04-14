from typing import ClassVar, Type, Union, cast

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.courses import (
    Course,
    CourseCreate,
    CourseDelete,
    CourseGet,
    CourseGetByIDQuery,
    CourseInfoUpdate,
    RecordedCourseDetailsUpdate,
)
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.courses import CourseRepository
from src.command.repositories.users import UserRepository
from src.command.services.base import BaseService
from src.events.events import CourseCreatedEvent, CourseDeletedEvent
from src.events.publishers import course_created_publisher, course_deleted_publisher
from src.exceptions import (
    CourseAlreadyExistsError,
    CourseNotFoundError,
    EntityNotFoundError,
    InvalidRoleError,
    UserNotFoundError,
)


class CourseService(BaseService[Course]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseNotFoundError
    _entity: ClassVar[Entity] = Entity.COURSE

    def __init__(
        self,
        repo: CourseRepository,
        user_repo: UserRepository,
        auth_service: AuthService,
    ) -> None:

        self.repo = repo
        self.user_repo = user_repo
        self.auth_service = auth_service

    async def _validate_trainer(self, trainer_id: int) -> None:

        user = await self.user_repo.get(UserGetByID(id=trainer_id))

        if user is None:
            raise UserNotFoundError(value=trainer_id, alias="Trainer")

        if user.role != UserRole.TRAINER:
            raise InvalidRoleError(role=UserRole.TRAINER)

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.COURSE,
        user_id_field="created_by",
        parent_id_field=None,  # Explicity set None, bacause course is the root.
        object_name="cmd",
    )
    async def create(self, cmd: CourseCreate) -> Course:
        # Check the course is alraedy exist with the given title.
        if await self.repo.exists_by(title=cmd.title):
            raise CourseAlreadyExistsError(value=cmd.title, identifier="title")

        await self._validate_trainer(trainer_id=cmd.trainer_id)

        course = await self.repo.add(cmd)

        if course is not None:
            # Publish the course created event.
            await course_created_publisher.publish(
                CourseCreatedEvent(
                    id=course.id,
                    created_by=course.created_by,  # type: ignore
                    trainer_id=course.trainer_id,
                )
            )
        return cast(Course, course)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.COURSE,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def update(
        self, cmd: Union[RecordedCourseDetailsUpdate, CourseInfoUpdate]
    ) -> Course:

        if isinstance(cmd, CourseInfoUpdate):
            if cmd.trainer_id is not None:
                await self._validate_trainer(trainer_id=cmd.trainer_id)
            course = await self.repo.update(cmd)
            return self._require_entity(course, value=cmd.id)

        else:
            course = await self.repo.update(cmd)
            return self._require_entity(course, value=cmd.id)

    @require_authorization(
        action=Action.DELETE,
        entity=Entity.COURSE,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def delete(self, cmd: CourseDelete):
        course = await self.repo.delete(cmd)

        if course is not None:
            # Publish the course deleted event.
            await course_deleted_publisher.publish(
                CourseDeletedEvent(
                    id=course.id,
                    deleted_by=course.deleted_by,  # type: ignore
                    trainer_id=course.trainer_id,
                )
            )
        return self._require_entity(course, value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: CourseGetByIDQuery):
        course = await self.repo.get(CourseGet(id=query.id))
        return self._require_entity(course, value=query.id)
