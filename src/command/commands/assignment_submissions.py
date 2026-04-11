from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional

from pydantic import Field

from src.command.commands.assignments import Assignment, NumberOfAttempts
from src.command.commands.base import (
    AssignmentBase,
    AssignmentID,
    AssignmentSubmissionBase,
    AuditFields,
    BaseCmd,
    MediaID,
    UserID,
)
from src.command.commands.media import AllowedContentTypes, Media

Feedback = Annotated[str, Field(max_length=2000)]
Score = int  # Temporary Fix
Attempt = NumberOfAttempts


class AllowedAssignmentSubmissionFileType(StrEnum):
    PDF = "application/pdf"


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


class AssignmentSubmission(
    AuditFields, AssignmentSubmissionCreateCore, AssignmentSubmissionBase
):
    score: Optional[Score] = None
    feedback: Optional[Feedback] = None
    status: AssignmentSubmissionStatus


class AssignmentSubmissionWithMedia(
    AssignmentSubmissionBase, AssignmentSubmissionCreateCore
):
    score: Optional[Score] = None
    feedback: Optional[Feedback] = None
    status: AssignmentSubmissionStatus
    submitted_at: datetime
    submitted_by: UserID
    submitter_name: str
    media_id: MediaID
    mime_type: AllowedContentTypes


class AssignmentSubmissionUploadURL(AssignmentSubmissionBase):
    media_id: MediaID
    upload_url: str


# NOTE: Delete is not in scope. Will implement later if required.


class AssignmentSubmissionContext(BaseCmd):
    assignment: Assignment
    submission: AssignmentSubmission
    media: Optional[Media] = None
