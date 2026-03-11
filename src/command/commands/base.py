from datetime import datetime
from functools import partial
from pydantic import BaseModel, Field, model_validator, BeforeValidator, TypeAdapter, PlainSerializer, field_serializer
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
    return cls(id=id).id


def to_external_id(
    id: ID,
    cls: Type["EntityBase"]
) -> str:
    """
        Helper function that takes EntityBase object and
        converts that as string with prefix.
        
        e.g., id 1 becomes U-1
    """
    obj = cls(id=id)
    return f"{cls.PREFIX}-{obj.id}"


class EntityBase(BaseModel):
    PREFIX: ClassVar[str] = "B"
    id: ID
    
    
    @model_validator(mode="after")
    def validate_id(self) -> Self:
        raw = str(self.id)
        parts = raw.split("-")

        # Allow "123" or "PREFIX-123", nothing else
        if len(parts) > 2:
            raise ValueError(f"Invalid id format: {raw!r}")

        number_part = parts[-1]
        if not number_part.isdigit() or number_part == "0":
            raise ValueError(f"ID number part must be a positive integer, got {number_part!r}")

        if len(parts) == 2:
            prefix = parts[0]
            if prefix != self.__class__.PREFIX:
                raise ValueError(f"Prefix should be {self.__class__.PREFIX!r}, got {prefix!r}")

        self.id = int(number_part)
        return self

    @field_serializer("id", return_type=str, when_used="json")
    def seriaize_id(self, id: ID):
        return f"{self.__class__.PREFIX}-{id}"
    
    
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
    
    
class AssignmentBase(EntityBase):
    PREFIX: ClassVar[str] = "A"
    

class EnrollmentBase(EntityBase):    
    PREFIX: ClassVar[str] = "E"


class MediaBase(EntityBase):
    PREFIX: ClassVar[str] = "ME"
    

class LessonBase(EntityBase):
    PREFIX: ClassVar[str] = "L"    

class AssignmentSubmissionBase(EntityBase):
    PREFIX: ClassVar[str] = "AS"


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

AssignmentID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=AssignmentBase)),
    PlainSerializer(partial(to_external_id, cls=AssignmentBase), when_used="json")
]

EnrollmentID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=EnrollmentBase)),
    PlainSerializer(partial(to_external_id, cls=EnrollmentBase), when_used="json")
]

MediaID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=MediaBase)),
    PlainSerializer(partial(to_external_id, cls=MediaBase), when_used="json")
]

LessonID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=LessonBase)),
    PlainSerializer(partial(to_external_id, cls=LessonBase), when_used="json")
]

AssignmentSubmissionID = Annotated[
    ID,
    BeforeValidator(partial(to_internal_id, cls=AssignmentSubmissionBase)),
    PlainSerializer(partial(to_external_id, cls=AssignmentSubmissionBase))
]


AnyID = Union[UserID, CourseID, ModuleID, AssignmentID, EnrollmentID]
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


class ReArrangeBase(BaseModel):
    target_id: ID
    preceding_id: Optional[ID]
    succeeding_id: Optional[ID]

    