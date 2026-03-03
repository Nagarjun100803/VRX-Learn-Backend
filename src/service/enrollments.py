import asyncio
from dataclasses import dataclass
from typing import Type, ClassVar
from src.commands.users import UserGetByID, UserRole
from src.repository.courses import CourseRepository
from src.repository.enrollments import EnrollmentRepository
from src.service.base import BaseService, require_access
from src.service.permission_policy import Entity
from src.dependencies import course_repository
from src.repository.enrollments import EnrollmentRepository
from src.commands.enrollments import (
    EnrollmentCreate, EnrollmentGet,
    EnrollmentUpdate, EnrollmentDelete, Enrollment
)
from src.exceptions import (
    EntityNotFoundError, EnrollmentAlreadyExistsError, 
    EnrollmentNotFoundError, CourseNotFoundError,
    UserNotFoundError, InvalidRoleError
)


@dataclass(kw_only=True)
class EnrollmentService(BaseService[Enrollment]):
    repo: EnrollmentRepository
    course_repo: CourseRepository
    
    # Class Variables.
    _entity: ClassVar[Entity] = Entity.ENROLLMENT
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = EnrollmentNotFoundError
    
    @require_access("create", user_id_alias="created_by", entity_id_alias="course_id", parent_repo=course_repository)
    async def create(self, cmd: EnrollmentCreate) -> Enrollment:
        # Check for course existance and duplicate enrollments.
        # TODO: Look for anyio or TaskGroup to run these for better concurrency.
        course_exist, user, duplicate_enrollment_flag, = await asyncio.gather(
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
            raise InvalidRoleError(message=f"'{user.role}' cannot enroll in a course. Role must be '{SUPPORTED_ROLES}'")
        
        if duplicate_enrollment_flag:
            raise EnrollmentAlreadyExistsError(
                value=(cmd.user_id, cmd.course_id),
                identifier=("user_id", "course_id")
            )
        
        return await self.repo.add(cmd)
        
    
    @require_access("update", user_id_alias="updated_by", entity_id_alias="id")
    async def update(self, cmd: EnrollmentUpdate) -> Enrollment:
        # NOTE: No checks added.
        return self._require_entity(
            await self.repo.update(cmd),
            value=cmd.id
        )
    
    
    @require_access("delete", user_id_alias="deleted_by", entity_id_alias="id")
    async def delete(self, cmd: EnrollmentDelete) -> Enrollment:
        # NOTE:  No checks added
        return self._require_entity(
            await self.repo.delete(cmd),
            value=cmd.id
        )
    
    
    @require_access("view", user_id_alias="viewer_id", entity_id_alias="id", obj_name="query")
    async def get(self, query: EnrollmentGet) -> Enrollment:
        return self._require_entity(
            await self.repo.get(query),
            value=query.id
        )
    
