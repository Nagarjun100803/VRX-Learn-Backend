from datetime import datetime
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Optional
from enum import StrEnum
from src.command.commands.base import AssignmentBase, AssignmentID, AuditFields, CourseID, UserID, NullField
from src.command.commands.validator import UpdateValidatorMixin


AssignmentTitle = Annotated[str, StringConstraints(min_length=5, max_length=250, to_upper=True)]
AssignmentInstruction = Annotated[str, Field(min_length=5, max_length=2000)]
NumberOfAttempts = Annotated[int, Field(le=3, gt=0)]
MaxScore = Annotated[int, Field(ge=5, le=100)]

class AllowedAssignmentFileType(StrEnum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOC = "application/msword"
    

class AssignmentCreateCore(BaseModel):
    title: AssignmentTitle
    instructions: Optional[AssignmentInstruction] = None
    course_id: CourseID
    due_date: Optional[datetime] = None
    max_score: MaxScore
    number_of_attempts: NumberOfAttempts = 1


class AssignmentCreate(AssignmentCreateCore):
    created_by: UserID
    
    
class AssignmentCreateWithPosition(AssignmentCreate):
    position_string: str
    
    
class AssignmentUpdateCore(UpdateValidatorMixin, BaseModel):
    title: Annotated[Optional[AssignmentTitle], NullField]
    instructions: Annotated[Optional[AssignmentInstruction], NullField]
    number_of_attempts: Annotated[Optional[NumberOfAttempts], NullField]
    

class AssignmentUpdate(AssignmentUpdateCore, AssignmentBase):
    updated_by: UserID
    

class AssignmentDelete(AssignmentBase):
    deleted_by: UserID
    

class AssignmentGet(AssignmentBase): ...

class AssignmentGetQuery(AssignmentGet):
    viewer_id: UserID
    

class AssignmentReArrangeCore(UpdateValidatorMixin, BaseModel):
    preceding_id: Annotated[Optional[AssignmentID], NullField]
    succeeding_id: Annotated[Optional[AssignmentID], NullField]

class AssignmentReArrange(AssignmentReArrangeCore):
    target_id: AssignmentID
    updated_by: UserID 
    

class AssignmentUploadUrl(AssignmentBase):
    upload_url: str


class Assignment(AuditFields, AssignmentCreate, AssignmentBase): ...