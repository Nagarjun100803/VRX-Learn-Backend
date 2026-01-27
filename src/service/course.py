import asyncio
from typing import Type, Union, Optional, override
from src.service.base import BaseService, require_access
from src.commands.courses import Course, CourseCreate, CourseDelete, CourseGet, CourseInfoUpdate, RecordedCourseDetailsUpdate, CourseGetByIDQuery
from src.repository.courses import CourseRepository
from src.service.permission_policy import Entity, PermissionPolicy
from src.exceptions import EntityNotFoundError, CourseNotFoundError, CourseAlreadyExistsError
from src.repository.users import UserRespository



class CourseService(BaseService[Course]):
    
    _not_found_exc: Type[EntityNotFoundError] = CourseNotFoundError
    _entity = Entity.COURSE
    

    def __init__(
        self, 
        user_repo: Optional[UserRespository] = None, # For user permissions.
        permission_policy: PermissionPolicy = None,
        repo: Optional[CourseRepository] = None
    ) -> None:
        
        super().__init__(user_repo, permission_policy)
        self.repo = repo or CourseRepository()
        
        
        
    @require_access(action="create", user_id_alias="created_by")
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
    

    @require_access(action="update", user_id_alias="updated_by", entity_id_alias="id")
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
            await asyncio.gather(*tuple(tasks))
            
            return await self.repo.update(cmd)
        
        course = await self.repo.update(cmd)
        return self._require_entity(course, value=cmd.id)
    
    
    @require_access(action="delete", user_id_alias="deleted_by", entity_id_alias="id")
    async def delete(self, cmd: CourseDelete):
        course = await self.repo.delete(cmd)
        return self._require_entity(course, value=cmd.id)
    
    
    @require_access(action="view", user_id_alias="viewer_id", entity_id_alias="id", obj_name="query")
    async def get(self, query: CourseGetByIDQuery):
        course = await self.repo.get(CourseGet(id=query.id))
        return self._require_entity(course, value=query.id)
    

