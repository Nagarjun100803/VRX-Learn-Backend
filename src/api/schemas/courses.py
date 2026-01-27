from typing import Annotated, Optional, Union
from pydantic import BaseModel, StringConstraints, Field
from src.commands.base import CourseID, UserID
from src.commands.courses import CourseCreateCore, RecordedCourseDetailsUpdateCore, CourseInfoUpdateCore  



class CourseCreateSchema(CourseCreateCore): ...
    

class CourseOutSchema(BaseModel):
    id: CourseID
    title: str
    slug: str
    trainer_id: UserID
    manager_id: UserID
    created_by: UserID
    

class CourseInfoUpdateSchema(CourseInfoUpdateCore): ...

class RecordedCourseDetailsUpdateSchema(RecordedCourseDetailsUpdateCore): ...
    
         

