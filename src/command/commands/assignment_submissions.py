from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional, Self

from pydantic import Field, model_validator

from src.command.commands.assignments import Assignment, NumberOfAttempts
from src.command.commands.base import (
    AssignmentBase,
    AssignmentID,
    AssignmentSubmissionBase,
    AssignmentSubmissionID,
    AuditFields,
    BaseAttachmentMetadata,
    BaseCmd,
    MediaID,
    UserID,
)
from src.command.commands.media import Media
from src.exceptions import FileSizeExceededError

Feedback = Annotated[str, Field(max_length=2000)]
Score = int  # Temporary Fix
Attempt = NumberOfAttempts


MAX_BYTES = int(5 * 1024 * 1024)  # 5MB


class AllowedAssignmentSubmissionAttachmentContentTypes(StrEnum):
    PDF = "application/pdf"


class AssignmentSubmissionAttachmentMetadata(
    BaseAttachmentMetadata[AllowedAssignmentSubmissionAttachmentContentTypes]
):
    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.size > MAX_BYTES:
            raise FileSizeExceededError(max_size=MAX_BYTES)
        return self


class AssignmentSubmissionStatus(StrEnum):
    SUBMITTED = "submitted"
    DONE_LATE = "done-late"
    GRADED = "graded"


class AssignmentSubmissionCreateCore(BaseCmd):
    assignment_id: AssignmentID


class AssignmentSubmissionCreate(AssignmentSubmissionCreateCore):
    created_by: UserID


class AssignmentSubmissionCreateWithAttemptAndStatus(AssignmentSubmissionCreate):
    # We change the status with `done_late` if late submission.
    status: AssignmentSubmissionStatus = AssignmentSubmissionStatus.SUBMITTED
    attempt: Attempt


class AssignmentSubmissionContext(AssignmentSubmissionCreateWithAttemptAndStatus):
    id: AssignmentSubmissionID


class AssignmentSubmissionVerifyCore(BaseCmd):
    score: Score
    feedback: Optional[Feedback] = None


class AssignmentSubmissionVerify(AssignmentSubmissionVerifyCore, AssignmentBase):
    updated_by: UserID


class AssignmentSubmissionVerifyWithStatus(AssignmentSubmissionVerify):
    status: AssignmentSubmissionStatus = AssignmentSubmissionStatus.GRADED


class AssignmentSubmissionFeedbackUpdateCore(BaseCmd):
    feedback: Feedback


class AssignmentSubmissionFeedbackUpdate(
    AssignmentSubmissionFeedbackUpdateCore, AssignmentSubmissionBase
):
    updated_by: UserID


class AssignmentSubmissionGetCore(AssignmentSubmissionBase): ...


class AssignmentSubmissionGet(AssignmentSubmissionGetCore):
    viewer_id: UserID


class AssignmentSubmissionAttachmentStatusUpdate(AssignmentSubmissionBase):
    updated_by: UserID


class AssignmentSubmission(
    AuditFields, AssignmentSubmissionCreateCore, AssignmentSubmissionBase
):
    attempt: Optional[int] = None
    score: Optional[Score] = None
    feedback: Optional[Feedback] = None
    status: AssignmentSubmissionStatus


class AssignmentSubmissionWithMedia(
    AssignmentSubmissionBase, AssignmentSubmissionCreateCore
):
    score: Optional[Score] = None
    max_score: int
    feedback: Optional[Feedback] = None
    attempt: int
    status: AssignmentSubmissionStatus
    submitted_at: datetime
    submitted_by: UserID
    submitter_name: str
    media_id: MediaID
    mime_type: AllowedAssignmentSubmissionAttachmentContentTypes
    filename: str


class AssignmentSubmissionDetail(
    AssignmentSubmissionCreateWithAttemptAndStatus, AssignmentSubmissionBase
): ...


# NOTE: Delete is not in scope. Will implement later if required.


class AssignmentSubmissionDetailContext(BaseCmd):
    assignment: Assignment
    submission: AssignmentSubmission
    media: Optional[Media] = None
