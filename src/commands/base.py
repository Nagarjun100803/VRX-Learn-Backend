from datetime import datetime
from functools import partial
from pydantic import BaseModel, Field, model_validator, BeforeValidator, TypeAdapter, PlainSerializer
from typing import ClassVar, Self, Type, Union, Optional, Annotated


ID = Union[int, str]

def to_internal_id(
    id: ID,
    cls: Type["EntityBase"]
) -> int:
    """
        Helper function that takes EntityBase object and
        converts that as integer.
        
        e.g., id U-1 becomes 1
    """
    return cls(id=id).remove_prefix().id


def to_external_id(
    id: ID,
    cls: Type["EntityBase"]
) -> str:
    """
        Helper function that takes EntityBase object and
        converts that as string with prefix.
        
        e.g., id 1 becomes U-1
    """
    return cls(id=id).add_prefix().id


class EntityBase(BaseModel):
    PREFIX: ClassVar[str] = "B"
    id: ID
    
    
    @model_validator(mode="after")
    def validate_id(self) -> Self:
    
        if not self.get_number_part().isdigit():
            raise ValueError("Value should be a number and should not have any decimal values.")
        
        prefix = self.get_prefix()
                
        if prefix and prefix != self.__class__.PREFIX:
            raise ValueError(f"Prefix should be {self.__class__.PREFIX}, got {prefix}")
        
        if not self.has_prefix():
            self.remove_prefix()
            
        return self

    def get_number_part(self) -> str:
        return str(self.id).split("-")[-1]

    def get_prefix(self) -> str | None:
        if not self.has_prefix():
            return None 
        return str(self.id).split("-")[0]

    def remove_prefix(self) -> Self:
        self.id = int(self.get_number_part())
        return self

    def has_prefix(self) -> bool:
        return "-" in str(self.id)
        
    def add_prefix(self) -> Self:
        if self.has_prefix():
            return self
        self.id = f"{self.__class__.PREFIX}-{self.id}"
        return self



class CourseBase(EntityBase):
    PREFIX: ClassVar[str] = "C"
       

class UserBase(EntityBase):
    PREFIX: ClassVar[str] = "U"
    

class ModuleBase(EntityBase):
    PREFIX: ClassVar[str] = "M"
    
    
class ResourceBase(EntityBase):
    PREFIX: ClassVar[str] = "R"
    

class EnrollmentBase(EntityBase):    
    PREFIX: ClassVar[str] = "E"


    
BaseID =  Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=EntityBase)),
    PlainSerializer(partial(to_external_id, cls=EntityBase), when_used="json") 
]   


UserID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=UserBase)),
    PlainSerializer(partial(to_external_id, cls=UserBase), when_used="json")
]


CourseID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=CourseBase)),
    PlainSerializer(partial(to_external_id, cls=CourseBase), when_used="json")
]


ModuleID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=ModuleBase)),
    PlainSerializer(partial(to_external_id, cls=ModuleBase), when_used="json")
]

ResourceID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=ResourceBase)),
    PlainSerializer(partial(to_external_id, cls=ResourceBase), when_used="json")
]

EnrollmentID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=EnrollmentBase)),
    PlainSerializer(partial(to_external_id, cls=EnrollmentBase), when_used="json")
]


AnyID = Union[UserID, CourseID, ModuleID, ResourceID, EnrollmentID]
any_id_adaptor = TypeAdapter(AnyID)



class CreateAuditFields(BaseModel):
    created_at: Optional[datetime] = None
    created_by: Optional[UserID] = None

class UpdateAuditFields(BaseModel):
    updated_at: Optional[datetime] = None
    updated_by: Optional[UserID] = None
    
class DeleteAuditField(BaseModel):
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UserID] = None
    
    
class AuditFields(DeleteAuditField, UpdateAuditFields, CreateAuditFields):
    """Helper class define the audit of the action."""


NullField = Field(default=None, examples=[None])
