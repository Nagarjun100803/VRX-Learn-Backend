from datetime import datetime
from typing import Annotated, Literal, Optional, Union
from pydantic import ConfigDict, Field, StringConstraints, BaseModel
from enum import Enum
from src.commands.base import CourseBase, UserID, AuditFields, NullField
from src.commands.validator import UpdateValidatorMixin



class CourseType(str, Enum):
    PRE_RECORDED = "pre-recorded"
    LIVE = "live"


class LiveCourseDetails(BaseModel):
    type: Literal[CourseType.LIVE] = CourseType.LIVE
    # We can add more fields, if we want.
    


CourseTitle = Annotated[str, StringConstraints(to_upper=True, min_length=10, strip_whitespace=True)]
CourseShortDescription = Annotated[str, StringConstraints(min_length=50)]
CourseLongDescription = Annotated[str, StringConstraints(min_length=50, max_length=600)] 
Price = Annotated[float, Field(gt=1000)]


class RecordedCourseDetails(BaseModel):
    type: Literal[CourseType.PRE_RECORDED] = CourseType.PRE_RECORDED
    total_hours: float
    price: Price


class CourseCreateCore(BaseModel): # Will act as mixin. used by Presentation layer [Fastapi]
    title: CourseTitle
    short_description: CourseShortDescription
    long_description: CourseLongDescription
    thumbnail: Optional[str] = None
    details: Union[RecordedCourseDetails, LiveCourseDetails] = Field(discriminator="type")
    trainer_id: UserID
    manager_id: UserID
    



class CourseCreate(CourseCreateCore):
    created_by: UserID

    def get_slug(self) -> str:
        return self.title.lower().strip().replace(" ", "-")
    
    

class CourseDelete(CourseBase): 
    deleted_by: UserID
    
  

class CourseInfoUpdateCore(UpdateValidatorMixin, BaseModel):
    title: Annotated[Optional[CourseTitle], NullField]
    short_description: Annotated[Optional[CourseShortDescription], NullField]
    long_description: Annotated[Optional[CourseLongDescription], NullField]
    thumbnail: Annotated[Optional[str], NullField]
    trainer_id: Annotated[Optional[UserID], NullField]
    manager_id: Annotated[Optional[UserID], NullField]
    
    
class CourseInfoUpdate(CourseInfoUpdateCore, CourseBase):
    updated_by: UserID

class RecordedCourseDetailsUpdateCore(UpdateValidatorMixin, BaseModel):
    total_hours: Annotated[Optional[float], NullField]
    price: Annotated[Optional[Price], NullField]
    


class RecordedCourseDetailsUpdate(RecordedCourseDetailsUpdateCore, CourseBase):
    updated_by: UserID    

class CourseGet(CourseBase): ...

class CourseGetByIDQuery(CourseGet):
    viewer_id: UserID


class Course(AuditFields, CourseCreate, CourseBase):
    slug: Annotated[Optional[str], NullField]
    
