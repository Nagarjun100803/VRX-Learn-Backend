import asyncio
from typing import ClassVar, Type, Union, override
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.users import UserRespository
from src.command.services.base import BaseService
from src.command.commands.courses import Course, CourseCreate, CourseDelete, CourseGet, CourseInfoUpdate, RecordedCourseDetailsUpdate, CourseGetByIDQuery
from src.command.repositories.courses import CourseRepository
from src.exceptions import EntityNotFoundError, CourseNotFoundError, CourseAlreadyExistsError, InvalidRoleError, UserNotFoundError
from src.auth import require_authorization, Entity, Action, AuthService


class CourseService(BaseService[Course]):
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseNotFoundError
    _entity: ClassVar[Entity] = Entity.COURSE
    
    def __init__(
        self,
        repo: CourseRepository,
        user_repo: UserRespository,
        auth_service: AuthService
    ) -> None:
        
        self.repo = repo
        self.user_repo = user_repo
        self.auth_service = auth_service
    
    
    async def _validate_course_participants(
        self,
        trainer_id: int,
        manager_id: int,
    ) -> None:
        
        trainer, manager = await asyncio.gather(
            self.user_repo.get(UserGetByID(id=trainer_id)),
            self.user_repo.get(UserGetByID(id=manager_id))
        )
        
        if trainer is None: raise UserNotFoundError(value=trainer_id, identifier="trainer")
        
        if manager is None: raise UserNotFoundError(value=manager_id, identifier="manager")
        
        if trainer.role != UserRole.TRAINER: raise InvalidRoleError(role=UserRole.TRAINER.value)
        
        if not manager.is_manager(): raise InvalidRoleError(role="manager")
        
        
    @require_authorization(
        action=Action.CREATE,
        entity=Entity.COURSE,
        user_id_field="created_by",
        parent_id_field=None, # Explicity set None, bacause course is the root.
        object_name="cmd"
    )
    @override
    async def create(self, cmd: CourseCreate):
        # Check the course is alraedy exist with the given title.
        if await self.repo.exists_by(title=cmd.title): 
            raise CourseAlreadyExistsError(value=cmd.title, identifier="title")
        
        await self._validate_course_participants(
            trainer_id=cmd.trainer_id,
            manager_id=cmd.manager_id
        )
        
        course = await self.repo.add(cmd)
        
        return course    
    

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.COURSE,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd"
    )
    @override
    async def update(
        self, 
        cmd: Union[
            RecordedCourseDetailsUpdate, 
            CourseInfoUpdate
        ]
    ) -> Course:
        
        if isinstance(cmd, CourseInfoUpdate):
            tasks = []
            if cmd.trainer_id is not None:
                tasks.append(self.validate_role("trainer",  cmd.trainer_id))
            if cmd.manager_id is not None:
                tasks.append(self.validate_role("manager", cmd.manager_id))
        
            # First execute the tasks to check for RoleError.
            await asyncio.gather(*tasks)
    
            return self._require_entity(await self.repo.update(cmd), value=cmd.id)
        
        course = await self.repo.update(cmd)
        return self._require_entity(course, value=cmd.id)
    
    
    @require_authorization(
        action=Action.DELETE,
        entity=Entity.COURSE,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd"
    )
    async def delete(self, cmd: CourseDelete):
        course = await self.repo.delete(cmd)
        return self._require_entity(course, value=cmd.id)
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query"
    )
    async def get(self, query: CourseGetByIDQuery):
        course = await self.repo.get(CourseGet(id=query.id))
        return self._require_entity(course, value=query.id)
    
