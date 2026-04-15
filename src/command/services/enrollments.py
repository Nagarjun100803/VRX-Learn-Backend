import asyncio
from typing import ClassVar, Type, cast

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.enrollments import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentDelete,
    EnrollmentGet,
    EnrollmentUpdate,
)
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.courses import CourseRepository
from src.command.repositories.enrollments import EnrollmentRepository
from src.command.repositories.users import UserRepository
from src.command.services.base import BaseService
from src.events.events import EnrollmentCreatedEvent, EnrollmentDeletedEvent
from src.events.publishers import (
    enrollment_created_publisher,
    enrollment_deleted_publisher,
)
from src.exceptions import (
    CourseNotFoundError,
    EnrollmentAlreadyExistsError,
    EnrollmentNotFoundError,
    EntityNotFoundError,
    InvalidRoleError,
    UserNotFoundError,
)


class EnrollmentService(BaseService[Enrollment]):
    def __init__(
        self,
        repo: EnrollmentRepository,
        user_repo: UserRepository,
        course_repo: CourseRepository,
        auth_service: AuthService,
    ) -> None:

        self.repo = repo
        self.user_repo = user_repo
        self.course_repo = course_repo
        self.auth_service = auth_service

    # Class Variables.
    _entity: ClassVar[Entity] = Entity.ENROLLMENT
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = EnrollmentNotFoundError

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.ENROLLMENT,
        user_id_field="created_by",
        parent_id_field=None,  # Explicitly set to None, because it is a root.
        object_name="cmd",
    )
    async def create(self, cmd: EnrollmentCreate) -> Enrollment:
        # Check for course existance and duplicate enrollments.
        # TODO: Look for anyio or TaskGroup to run these for better concurrency.
        course_exist, user, duplicate_enrollment_flag = await asyncio.gather(
            self.course_repo.exists_by(id=cmd.course_id),
            self.user_repo.get(UserGetByID(id=cmd.user_id)),
            self.repo.exists_by(user_id=cmd.user_id, course_id=cmd.course_id),
        )

        if not course_exist:
            raise CourseNotFoundError(value=cmd.course_id)

        if user is None:
            raise UserNotFoundError(value=cmd.user_id)

        SUPPORTED_ROLES = (UserRole.TRAINEE.value, UserRole.TRAINER.value)
        if user.role not in SUPPORTED_ROLES:
            raise InvalidRoleError(
                message=f"'{user.role}' cannot enroll in a course. Role must be '{SUPPORTED_ROLES}'"
            )

        if duplicate_enrollment_flag:
            raise EnrollmentAlreadyExistsError(
                value=(cmd.user_id, cmd.course_id), identifier=("user_id", "course_id")
            )

        enrollment = await self.repo.add(cmd)

        if enrollment is not None:
            # Publish the enrollment created event.
            await enrollment_created_publisher.publish(
                EnrollmentCreatedEvent(
                    id=enrollment.id, created_by=enrollment.created_by
                )  # type: ignore
            )

        return cast(Enrollment, enrollment)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.ENROLLMENT,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def update(self, cmd: EnrollmentUpdate) -> Enrollment:
        # NOTE: No checks added.
        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    @require_authorization(
        action=Action.DELETE,
        entity=Entity.ENROLLMENT,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def delete(self, cmd: EnrollmentDelete) -> Enrollment:
        # NOTE:  No checks added
        enrollment = await self.repo.delete(cmd)

        if enrollment is not None:
            # Publish the enrollment deleted event.
            await enrollment_deleted_publisher.publish(
                EnrollmentDeletedEvent(
                    id=enrollment.id, deleted_by=enrollment.deleted_by
                )  # type: ignore
            )

        return self._require_entity(enrollment, value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ENROLLMENT,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: EnrollmentGet) -> Enrollment:
        return self._require_entity(await self.repo.get(query), value=query.id)
