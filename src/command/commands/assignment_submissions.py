from typing import Annotated, Optional
from pydantic import BaseModel, Field
from enum import StrEnum
from src.command.commands.base import AssignmentBase, AssignmentID, AssignmentSubmissionBase, AuditFields, UserID
from src.command.commands.assignments import Assignment, MaxScore, NumberOfAttempts
from src.command.commands.media import Media


Feedback = Annotated[str, Field(max_length=2000)]
Score = int # Temporary Fix
Attempt = NumberOfAttempts

class AllowedAssignmentSubmissionFileType(StrEnum):
    PDF = "application/pdf"


class AssignmentSubmissionStatus(StrEnum):
    SUBMITTED = "submitted"
    DONE_LATE = "done-late"
    GRADED = "graded"
    

class AssignmentSubmissionCreateCore(BaseModel):
    assignment_id: AssignmentID
    

class AssignmentSubmissionCreate(AssignmentSubmissionCreateCore):
    created_by: UserID
    

class AssignmentSubmissionCreateWithAttemptAndStatus(AssignmentSubmissionCreate):
    # We change the status with `done_late` if late submission.
    status: AssignmentSubmissionStatus = AssignmentSubmissionStatus.SUBMITTED
    attempt: Attempt


class AssignmentSubmissionVerifyCore(BaseModel):
    score: MaxScore
    feedback: Optional[Feedback] = None


class AssignmentSubmissionVerify(AssignmentSubmissionVerifyCore, AssignmentBase):
    updated_by: UserID
    
class AssignmentSubmissionVerifyWithStatus(AssignmentSubmissionVerify):
    status: AssignmentSubmissionStatus = AssignmentSubmissionStatus.GRADED
    

class AssignmentSubmissionFeedbackUpdateCore(BaseModel):
    feedback: Feedback
    

class AssignmentSubmissionFeedbackUpdate(AssignmentSubmissionFeedbackUpdateCore, AssignmentSubmissionBase):
    updated_by: UserID
    

class AssignmentSubmissionGetCore(AssignmentSubmissionBase): ...


class AssignmentSubmissionGet(AssignmentSubmissionGetCore):
    viewer_id: UserID


class AssignmentSubmission(AuditFields, AssignmentSubmissionCreateCore, AssignmentSubmissionBase):
    score: Optional[Score]
    feedback: Optional[Feedback]
    status: AssignmentSubmissionStatus



class AssignmentSubmissionUploadURL(AssignmentSubmissionBase):
    upload_url: str


# NOTE: Delete is not in scope. Will implement later if required.

class AssignmentSubmissionContext(BaseModel):
    assignment: Assignment
    submission: AssignmentSubmission
    media: Optional[Media] = None
