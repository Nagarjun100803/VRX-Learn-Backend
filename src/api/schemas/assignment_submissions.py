from datetime import datetime
from typing import Optional

from src.command.commands.assignment_submissions import (
    AssignmentSubmissionBase,
    AssignmentSubmissionCreateCore,
    AssignmentSubmissionFeedbackUpdateCore,
    AssignmentSubmissionStatus,
    AssignmentSubmissionVerifyCore,
    Score,
)
from src.command.commands.base import AssignmentID, BaseCmd, UserID
from src.command.services.files import FileMetadata


class AssignmentSubmissionOut(AssignmentSubmissionBase):
    assignment_id: AssignmentID
    status: AssignmentSubmissionStatus
    score: Optional[Score] = None
    created_by: UserID
    created_at: datetime


class AssignmentSubmissionCreateSchema(BaseCmd):
    assignment_submission: AssignmentSubmissionCreateCore
    file_metadata: FileMetadata


class AssignmentSubmissionVerifySchema(AssignmentSubmissionVerifyCore): ...


class AssignmentSubmissionFeedbackUpdateSchema(
    AssignmentSubmissionFeedbackUpdateCore
): ...
