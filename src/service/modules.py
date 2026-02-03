import asyncio
from typing import Type, Optional, ClassVar
from dataclasses import dataclass
from src.repository.users import UserRespository
from src.service.base import BaseService, require_access
from src.repository.modules import ModuleRepository
from src.repository.courses import CourseRepository
from src.commands.modules import Module, ModuleCreate, ModuleCreateWithPosition, ModuleGetQuery, ModuleUpdate, ModuleDelete, ModuleGet, ReArrangeModule
from src.service.permission_policy import Entity, PermissionPolicy
from src.exceptions import EntityNotFoundError, CourseModuleNotFoundError, CourseNotFoundError, CourseModuleAlreadyExistsError


course_repository = CourseRepository()
# NOTE: Need to create all singleton in a file, and import.

@dataclass
class ModuleService(BaseService[Module]):
    
    _entity: ClassVar[Entity] = Entity.MODULE
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseModuleNotFoundError
    
    course_repo: CourseRepository
    repo: ModuleRepository
    
            
     
    @require_access(action="create", user_id_alias="created_by", entity_id_alias="course_id", parent_repo=course_repository)    
    async def create(self, cmd: ModuleCreate):
        
        # Conditions
        course_exist_flag, duplicate_module_title_flag = await asyncio.gather(
            self.course_repo.exists_by(id=cmd.course_id),
            self.repo.exists_by(title=cmd.title, course_id=cmd.course_id)
        )
        # Check for course existance.
        if not course_exist_flag:
            raise CourseNotFoundError(value=cmd.course_id)
            
        # Check for duplicate module name in a course.
        if duplicate_module_title_flag:
            raise CourseModuleAlreadyExistsError(cmd.title, identifier="title")
                 
        
        position_string = await self.generate_position_string(course_id=cmd.course_id)
                 
        module = await self.repo.add(
            ModuleCreateWithPosition(
                **cmd.model_dump(),
                position_string=position_string
            )
        )
        return self._require_entity(module)
    


    @require_access(action="update", user_id_alias="updated_by", entity_id_alias="id")
    async def update(self, cmd: ModuleUpdate):
        module = await self.repo.update(cmd)
        return self._require_entity(module, value=cmd.id)
    
   
    
    @require_access(action="delete", user_id_alias="deleted_by", entity_id_alias="id")
    async def delete(self, cmd: ModuleDelete):
        module = await self.repo.delete(cmd)
        return self._require_entity(module, value=cmd.id)
    
    
    
    @require_access(action="view", user_id_alias="viewer_id", entity_id_alias="id", obj_name="query")
    async def get(self, query: ModuleGetQuery):
        module = await self.repo.get(query)
        return self._require_entity(module, value=query.id)
    

    @require_access(action="update", user_id_alias="updated_by", entity_id_alias="target_id")
    async def rearrange_sequence(
        self, cmd: ReArrangeModule, 
        scope: str = "course_id"
    ) -> str: 
                
        return await super().rearrange_sequence(cmd, scope)
