from datetime import datetime
from typing import Optional

from src.command.commands.assignment_submissions import (
    AssignmentSubmissionStatus,
    Attempt,
    Score,
)
from src.command.commands.assignments import (
    AssignmentInstruction,
    AssignmentTitle,
    MaxScore,
    NumberOfAttempts,
)
from src.command.commands.base import AssignmentID, AssignmentSubmissionID, MediaID
from src.command.commands.media import AllowedContentTypes
from src.query.dto.base import BaseDTO, PageMeta
from src.query.dto.entity_list import (
    AssignmentSubmissionDetail,
    AssignmentSubmissionFilters,
)


class TraineeAssignmentCore(BaseDTO):
    id: AssignmentID
    title: AssignmentTitle
    is_completed: bool = False
    """
        `is_completed` represents, the trainee submitted the assignments atleast one time.
    """


class TrainerAssignmentCore(BaseDTO):
    id: AssignmentID
    title: AssignmentTitle
    due_date: Optional[datetime] = None


class AssignmentDetail(BaseDTO):
    id: AssignmentID
    title: AssignmentTitle
    instructions: Optional[AssignmentInstruction] = None
    due_date: Optional[datetime] = None
    max_score: MaxScore
    number_of_attempts: NumberOfAttempts


class AssignmentAttachment(BaseDTO):
    media_id: MediaID
    mime_type: AllowedContentTypes
    filename: str


class TraineeSubmissionDetail(BaseDTO):
    id: AssignmentSubmissionID
    filename: str
    score: Optional[Score] = None
    status: AssignmentSubmissionStatus
    attempt: Attempt
    feedback: Optional[str] = None
    submitted_at: datetime
    media_id: MediaID
    mime_type: AllowedContentTypes


class TrainerAssignmentContent(BaseDTO):
    assignment: AssignmentDetail
    attachment: Optional[AssignmentAttachment] = None


class TraineeAssignmentContent(TrainerAssignmentContent):
    submissions: list[TraineeSubmissionDetail]  # His own works.


class TrainerSubmissionDetail(AssignmentSubmissionDetail): ...


class AssignmentSubmissionQuerySchema(AssignmentSubmissionFilters, PageMeta): ...
