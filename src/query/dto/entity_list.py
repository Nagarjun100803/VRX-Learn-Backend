from datetime import datetime
from typing import Optional

from src.command.commands.assignments import AssignmentTitle
from src.command.commands.base import AssignmentID, AssignmentSubmissionID, LessonID, ModuleID
from src.command.commands.lessons import LessonTitle
from src.command.commands.modules import ModuleTitile
from src.query.dto.base import BaseDTO



class ModuleDetail(BaseDTO):
    id: ModuleID
    title: ModuleTitile
    


class LessonDetail(BaseDTO):
    id: LessonID
    title: LessonTitle
    
    

class AssignmentDetail(BaseDTO):
    id: AssignmentID
    title: AssignmentTitle
    
    

class AssignmentDetailWithDue(AssignmentDetail):
    due_date: Optional[datetime] = None


    