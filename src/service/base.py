import inspect
from functools import wraps
from typing import Any, Callable, Literal, Optional, Type, ClassVar, TypeVar, ParamSpec
from abc import ABC, abstractmethod
from pydantic import BaseModel
from src.exceptions import EntityNotFoundError, UnauthorizedError, InvalidRoleError, UserNotFoundError, ValidationError
from src.repository.base import BaseRepository, ReorderParicipants
from src.service.permission_policy import Action, Entity, PermissionPolicy, UserRole, UserRoleOrVirtual
from src.repository.users import UserRespository
from src.commands.users import UserGetByID
from src.commands.base import UserID, ReArrangeBase
from src.service.fractional_index import fractional_index


E = TypeVar("E", bound=EntityNotFoundError)
P = ParamSpec("P")
R = TypeVar("R")



def require_access(
    action: Action,
    user_id_alias: str,
    entity_id_alias: Optional[str] = None,
    parent_repo: Optional[BaseRepository] = None,
    obj_name: Literal["cmd", "query"] = "cmd" # type: ignore
    ):
        
    def dec(func: Callable[P, R]) -> Callable[P, R]:
        # Get the function signature only once.
        sig = inspect.signature(func)
        @wraps(func)
        async def wrapper(self: BaseService, *args: P.args, **kwargs: P.kwargs) -> R:
            # Bind the parameter to this wrapper function.
            bound_arguments = sig.bind(self, *args, **kwargs)
            bound_arguments.apply_defaults()
            
            # Check the obj_name is found in function signature as parameter.
            obj = bound_arguments.arguments.get(obj_name)
            if obj is None:
                raise ValueError(f"Argument {obj_name} was not found in function call.")
            
            # Get the enities from the object.
            user_id = getattr(obj, user_id_alias, None)
            entity_id = getattr(obj, entity_id_alias or "", None)
            
    
            # Check the action Type.
            if user_id is None:
                raise AttributeError(f"The object {obj_name} is missing required attribute '{user_id_alias}'")
            if action != Action.CREATE and entity_id is None:
                raise AttributeError(f"The object {obj_name} is missing required attribute {entity_id_alias} to check permission.")
            
            # Now check the user is exist to perform the action.
            actor = await self.user_repo.get(UserGetByID(id=user_id))
            if not actor:
                raise UnauthorizedError()
            
            if actor.role == UserRole.ADMIN:
                return await func(self, *args, **kwargs)
            
            policy = self.permission_policy.get_policy(actor.role, self._entity)
            if not policy.allows(action):
                raise UnauthorizedError()
            
            # This self.repo refers actual entity's repo. 
            # it may be course, enrollement based on runtime.
            
            # Choose which repo to use to check the ownership.
            repo = parent_repo if parent_repo is not None else self.repo
            if (
                    (policy.scope == "specific") and 
                    (not await repo.verify_ownership(entity_id=entity_id, user_id=user_id)
                    
                )
            ): 
                raise UnauthorizedError()
            
            return await func(self, *args, **kwargs)
 
        return wrapper
    
    return dec
        



class BaseService[T](ABC):
    
    """
        Base class for all the service. Do not use it directly.
    """

    _not_found_exc: ClassVar[Type[E]] 
    _entity: Entity
    
    def __init__(
        self,
        user_repo: Optional[UserRespository] = None,
        permission_policy: Optional[PermissionPolicy] = None
    ):
        super().__init__() 
        self.user_repo = user_repo or UserRespository()
        self.permission_policy = permission_policy or PermissionPolicy()


    def _require_entity(self, entity: Optional[T], **error_kwargs) -> T:
        """
            Helper function that return the entity if not None. 
            Otherwise it raise NotFoundError.
        """
        if entity is None:
            raise self._not_found_exc(**error_kwargs)
        return entity
          
    
    async def validate_role(
        self,
        role: UserRoleOrVirtual,
        user_id: UserID
    ) -> None:

        exc = InvalidRoleError(role)
        user = await self.user_repo.get(UserGetByID(id=user_id))
        if user is None:
            raise UserNotFoundError(
                value=user_id, identifier="id", alias=role
            )
    
        # Virtual role mappings.
        virtual_role_mappings = {
            "manager": {UserRole.SUBADMIN, UserRole.TRAINER}
        }
          
        if role in virtual_role_mappings:
            is_valid = user.role in virtual_role_mappings[role]
            
        else:
            is_valid = user.role == role
            
        if not is_valid:
            raise exc
       
       
    async def generate_position_string(self, **scope_kwargs: dict[str, Any]) -> str:
        current_max = await self.repo.get_max_position_string(**scope_kwargs)
        new_key = fractional_index.generate_key(current_max, None)
        print(f"Current key : {current_max} and new key is {new_key}")
        return new_key
    
    
    async def rearrange_sequence(
        self, 
        cmd: ReArrangeBase, 
        scope: str
        ):
        
        # Get the participants data.
        participants_data: ReorderParicipants = await self.repo.get_reorder_participants(
            participants=cmd, scope=scope
        )
        
        if not participants_data.target:  # TODO: Need to check for absence preceding or succeeding if required.
            raise EntityNotFoundError(f"{self._entity} is not found to perform reorder.")

        target_scope = participants_data.target.scope
        for participant in [participants_data.preceding, participants_data.succeeding]:
            if participant and participant.scope != target_scope:
                raise ValidationError(f"All participants should belongs to same {scope} = '{target_scope}'")

        # Generate the new position string.
        position_string = fractional_index.generate_key(*participants_data.position_string_pairs())
        
        # Update this to DB by calling a repo.
        updated_entity = await self.repo.update_position(
            target_id=cmd.target_id,
            position_string=position_string
        )
        
        if not updated_entity:
            raise EntityNotFoundError(f"{self._entity} is not found to update position string.")

        return updated_entity
    

    @abstractmethod
    async def create(self, cmd: BaseModel) -> T:
        """Create a new entity"""

    
    @abstractmethod
    async def update(self, cmd: BaseModel) -> T:
        """Modify the existing entity"""
      
    @abstractmethod  
    async def delete(self, cmd: BaseModel) -> T:
        """Remove the entity"""
        
    @abstractmethod
    async def get(self, query: BaseModel) -> T:
        "Get a specific entity if exists or raise error"
    
