from abc import ABC, abstractmethod
from typing import ClassVar, Literal, Optional, Type, TypeAlias, TypeVar, Union

from pydantic import BaseModel

from src.exceptions import EntityNotFoundError
from src.command.commands.users import UserRole
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
        
