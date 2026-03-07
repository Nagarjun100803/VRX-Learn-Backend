import asyncio
from typing import Type, ClassVar
from dataclasses import dataclass
from src.service.base import BaseService
from src.repository.modules import ModuleRepository
from src.repository.courses import CourseRepository
from src.commands.modules import Module, ModuleCreate, ModuleCreateWithPosition, ModuleGetQuery, ModuleUpdate, ModuleDelete, ModuleGet, ReArrangeModule
from src.exceptions import EntityNotFoundError, CourseModuleNotFoundError, CourseNotFoundError, CourseModuleAlreadyExistsError
from src.auth import AuthService, Entity, Action, require_authorization


@dataclass(kw_only=True)
class ModuleService(BaseService[Module]):
    
    _entity: ClassVar[Entity] = Entity.MODULE
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseModuleNotFoundError
    
    course_repo: CourseRepository
    repo: ModuleRepository
    auth_service: AuthService
    
            
     
    @require_authorization(
        action=Action.CREATE,
        entity=Entity.MODULE,
        user_id_field="created_by",
        parent_id_field="course_id",
        object_name="cmd"
    )
    async def create(self, cmd: ModuleCreate) -> Module:
        
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
    


    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.MODULE,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd"
    )
    async def update(self, cmd: ModuleUpdate) -> Module:
        # Get the module.
        module = await self.repo.pick(columns=("id", "title", "course_id"), id=cmd.id)
        if module is None:
            raise CourseModuleNotFoundError(value=cmd.id)
        
        # Check for title change.
        if cmd.title != module["title"]:
            duplicate_title_flag = await self.repo.exists_by(title=cmd.title, course_id=module["course_id"])
            if duplicate_title_flag:
                raise CourseModuleAlreadyExistsError(value=cmd.title, identifier="title")
            
        # Update the fields.
        return self._require_entity(
            await self.repo.update(cmd),
            value=cmd.id
        )
            
    
   
    
    @require_authorization(
        action=Action.DELETE,
        entity=Entity.MODULE,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd"
    )
    async def delete(self, cmd: ModuleDelete) -> Module:
        module = await self.repo.delete(cmd)
        return self._require_entity(module, value=cmd.id)
    
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.MODULE,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query"
    )
    async def get(self, query: ModuleGetQuery) -> Module:
        module = await self.repo.get(query)
        return self._require_entity(module, value=query.id)
    

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.MODULE,
        user_id_field="updated_by",
        entity_id_field="target_id"
    )
    async def rearrange_sequence(
        self, cmd: ReArrangeModule, 
        scope: str = "course_id"
    ) -> Module: 
                
        return await super().rearrange_sequence(cmd, scope)
