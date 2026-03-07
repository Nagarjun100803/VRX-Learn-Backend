import asyncio
from typing import ClassVar, Type, Union, override
from src.service.base import BaseService
from src.commands.courses import Course, CourseCreate, CourseDelete, CourseGet, CourseInfoUpdate, RecordedCourseDetailsUpdate, CourseGetByIDQuery
from src.repository.courses import CourseRepository
from src.exceptions import EntityNotFoundError, CourseNotFoundError, CourseAlreadyExistsError
from dataclasses import dataclass
from src.auth import require_authorization, Entity, Action, AuthService


@dataclass(kw_only=True)
class CourseService(BaseService[Course]):
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseNotFoundError
    _entity: ClassVar[Entity] = Entity.COURSE
    repo: CourseRepository
    auth_service: AuthService
        
        
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
        
        await asyncio.gather(
                self.validate_role("trainer", cmd.trainer_id),
                self.validate_role("manager", cmd.manager_id)
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
    
