from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional, Self

from pydantic import Field, StringConstraints, model_validator

from src.command.commands.base import (
    AssignmentBase,
    AssignmentID,
    AuditFields,
    BaseAttachmentMetadata,
    BaseCmd,
    CourseID,
    MediaID,
    NullField,
    UserID,
)
from src.command.commands.validator import UpdateValidatorMixin
from src.exceptions import FileSizeExceededError

# Types
type AssignmentTitle = Annotated[
    str, StringConstraints(min_length=1, max_length=250, to_upper=True)
]
type AssignmentInstruction = Annotated[str, Field(max_length=5000)]
type NumberOfAttempts = Annotated[int, Field(le=3, gt=0)]
type MaxScore = Annotated[int, Field(ge=5, le=100)]


MAX_BYTES = int(2.5 * 1024 * 1024 * 1024)


class AllowedAssignmentAttachmentContentTypes(StrEnum):
    PDF = "application/pdf"


class AssignmentAttachmentMetadata(
    BaseAttachmentMetadata[AllowedAssignmentAttachmentContentTypes]
):
    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.size > MAX_BYTES:
            raise FileSizeExceededError(max_size=MAX_BYTES)
        return self


class AssignmentCreateCore(BaseCmd):
    title: AssignmentTitle
    instructions: Optional[AssignmentInstruction] = None
    course_id: CourseID
    due_date: Optional[datetime] = None
    max_score: MaxScore
    number_of_attempts: NumberOfAttempts = 1


class AssignmentCreate(AssignmentCreateCore):
    created_by: UserID


class AssignmentAttachmentUploadContext(AssignmentCreate):
    id: AssignmentID
    created_at: datetime
    media_id: MediaID
    url: str


class AssignmentAttachmentStatusUpdate(AssignmentBase):
    updated_by: UserID


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


class Assignment(AuditFields, AssignmentCreateCore, AssignmentBase): ...
