from datetime import datetime
from typing import Optional

from src.command.commands.assignment_submissions import (
    AssignmentSubmissionAttachmentMetadata,
    AssignmentSubmissionBase,
    AssignmentSubmissionFeedbackUpdateCore,
    AssignmentSubmissionStatus,
    AssignmentSubmissionVerifyCore,
    Feedback,
    Score,
)
from src.command.commands.base import AssignmentID, BaseCmd, UserID


class AssignmentSubmissionOut(AssignmentSubmissionBase):
    assignment_id: AssignmentID
    status: AssignmentSubmissionStatus
    score: Optional[Score] = None
    feedback: Optional[Feedback] = None
    created_by: UserID
    created_at: datetime


class AssignmentSubmissionCreateSchema(BaseCmd):
    assignment_id: AssignmentID
    attachment: AssignmentSubmissionAttachmentMetadata


class AssignmentSubmissionVerifySchema(AssignmentSubmissionVerifyCore): ...


class AssignmentSubmissionFeedbackUpdateSchema(
    AssignmentSubmissionFeedbackUpdateCore
): ...
