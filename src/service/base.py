from typing import Any, Literal, Optional, Type, ClassVar, TypeAlias, TypeVar, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel
from src.exceptions import EntityNotFoundError, ValidationError
from src.repository.base import BaseRepository, ReorderParicipants
from src.commands.base import ReArrangeBase
from src.service.fractional_index import fractional_index
from src.commands.users import UserRole
from src.auth import Entity



E = TypeVar("E", bound=EntityNotFoundError)

UserRoleOrVirtual: TypeAlias = Union[UserRole, Literal["manager"]]

class BaseService[T](ABC):
    
    """
        Base class for all the service. Do not use it directly.
    """

    _not_found_exc: ClassVar[Type[E]] 
    _entity: ClassVar[Entity]
    


    def _require_entity(self, entity: Optional[T], **error_kwargs) -> T:
        """
            Helper function that return the entity if not None. 
            Otherwise it raise NotFoundError.
        """
        if entity is None:
            raise self._not_found_exc(**error_kwargs)
        return entity
          
           
    # TODO: Need to refactor this into Rearrange Service.
    async def generate_position_string(self, **scope_kwargs: dict[str, Any]) -> str:
        current_max = await self.repo.get_max_position_string(**scope_kwargs)
        new_key = fractional_index.generate_key(current_max, None)
        print(f"Current key : {current_max} and new key is {new_key}")
        return new_key
    
    
    async def rearrange_sequence(
        self, 
        cmd: ReArrangeBase, 
        scope: str
        ) -> T:
        
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
        
