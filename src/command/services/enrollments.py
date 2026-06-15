import asyncio
from typing import ClassVar, Optional, Type

from asyncpg import Connection

from src.auth import Entity
from src.command.commands.enrollments import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentCreateWithRestrictions,
    EnrollmentDelete,
    EnrollmentGet,
    EnrollmentModuleRestrictionSync,
    EnrollmentUpdate,
)
from src.command.commands.module_restrictions import ModuleRestrictionSync
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.courses import CourseRepository
from src.command.repositories.enrollments import EnrollmentRepository
from src.command.repositories.users import UserRepository
from src.command.services.base import BaseService
from src.command.services.module_restrictions import ModuleAccessService
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
        module_access_service: ModuleAccessService,
    ) -> None:
        self.repo = repo
        self.user_repo = user_repo
        self.course_repo = course_repo
        self.module_access_service = module_access_service

    # Class Variables.
    _entity: ClassVar[Entity] = Entity.ENROLLMENT
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = EnrollmentNotFoundError

    async def _validate_create(self, cmd: EnrollmentCreateWithRestrictions) -> None:
        # Check for course existence and duplicate enrollments.
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

    async def create(self, cmd: EnrollmentCreateWithRestrictions) -> Enrollment:
        await self._validate_create(cmd)

        async with self.repo.db.transaction() as tconn:
            enrollment = await self.repo.add(
                cmd=EnrollmentCreate(**cmd.model_dump()), connection=tconn
            )
            if cmd.restricted_module_ids:
                await self.module_access_service.sync_restriction(
                    cmd=ModuleRestrictionSync(
                        enrollment_id=enrollment.id,
                        module_ids=cmd.restricted_module_ids,
                        by=cmd.created_by,
                    ),
                    connection=tconn,
                )
        return enrollment

    async def sync_module_restriction(
        self,
        cmd: EnrollmentModuleRestrictionSync,
        connection: Optional[Connection] = None,
    ) -> None:

        await self.module_access_service.sync_restriction(
            cmd=ModuleRestrictionSync(
                enrollment_id=cmd.enrollment_id,
                module_ids=cmd.module_ids,
                by=cmd.updated_by,
            ),
            connection=connection,
        )

    async def update(self, cmd: EnrollmentUpdate) -> Enrollment:
        # NOTE: No checks added.
        return self._require_entity(await self.repo.update(cmd), value=cmd.id)

    async def delete(self, cmd: EnrollmentDelete) -> Enrollment:
        # NOTE:  No checks added
        return self._require_entity(await self.repo.delete(cmd), value=cmd.id)

    async def get(self, query: EnrollmentGet) -> Enrollment:
        return self._require_entity(await self.repo.get(query), value=query.id)
