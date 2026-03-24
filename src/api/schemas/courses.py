from src.command.commands.base import BaseCmd, CourseID, UserID
from src.command.commands.courses import CourseCreateCore, RecordedCourseDetailsUpdateCore, CourseInfoUpdateCore  



class CourseCreateSchema(CourseCreateCore): ...
    

class CourseOutSchema(BaseCmd):
    id: CourseID
    title: str
    slug: str
    trainer_id: UserID
    manager_id: UserID
    created_by: UserID
    

class CourseInfoUpdateSchema(CourseInfoUpdateCore): ...

class RecordedCourseDetailsUpdateSchema(RecordedCourseDetailsUpdateCore): ...
    
         

