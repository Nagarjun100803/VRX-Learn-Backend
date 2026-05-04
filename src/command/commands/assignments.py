from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional

from pydantic import Field, StringConstraints

from src.command.commands.base import (
    AssignmentBase,
    AssignmentID,
    AuditFields,
    BaseCmd,
    CourseID,
    NullField,
    UserID,
)
from src.command.commands.media import MediaDetail
from src.command.commands.validator import UpdateValidatorMixin

AssignmentTitle = Annotated[
    str, StringConstraints(min_length=1, max_length=250, to_upper=True)
]
AssignmentInstruction = Annotated[str, Field(max_length=5000)]
NumberOfAttempts = Annotated[int, Field(le=3, gt=0)]
MaxScore = Annotated[int, Field(ge=5, le=100)]


class AllowedAssignmentFileType(StrEnum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOC = "application/msword"


class AssignmentCreateCore(BaseCmd):
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


class AssignmentUpdateCore(UpdateValidatorMixin, BaseCmd):
    title: Annotated[Optional[AssignmentTitle], NullField]
    instructions: Annotated[Optional[AssignmentInstruction], NullField]
    due_date: Annotated[Optional[datetime], NullField]


class AssignmentUpdate(AssignmentUpdateCore, AssignmentBase):
    updated_by: UserID


class AssignmentDelete(AssignmentBase):
    deleted_by: UserID


class AssignmentGet(AssignmentBase): ...


class AssignmentGetQuery(AssignmentGet):
    viewer_id: UserID


class AssignmentReArrangeCore(UpdateValidatorMixin, BaseCmd):
    preceding_id: Annotated[Optional[AssignmentID], NullField]
    succeeding_id: Annotated[Optional[AssignmentID], NullField]


class AssignmentReArrange(AssignmentReArrangeCore):
    target_id: AssignmentID
    updated_by: UserID


class AssignmentDetail(AssignmentBase, AssignmentCreate):
    created_at: datetime


class AssignmentUpload(BaseCmd):
    assignment: AssignmentDetail
    media: MediaDetail


class Assignment(AuditFields, AssignmentCreateCore, AssignmentBase): ...
