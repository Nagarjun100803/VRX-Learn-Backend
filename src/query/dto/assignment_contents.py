from datetime import date, datetime
from typing import Literal, Optional

from src.command.commands.assignment_submissions import AssignmentSubmissionStatus, Attempt, Score
from src.command.commands.assignments import AssignmentInstruction, AssignmentTitle, MaxScore, NumberOfAttempts
from src.command.commands.base import AssignmentID, AssignmentSubmissionID, MediaID
from src.command.commands.users import Email
from src.query.dto.base import BaseDTO


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
    max_attempts: NumberOfAttempts


class AssignmentAttachment(BaseDTO):
    media_id: MediaID
    filename: str


class TraineeSubmissionDetail(BaseDTO):
    id: AssignmentSubmissionID
    filename: str
    score: Optional[Score] = None
    status: AssignmentSubmissionStatus
    attempt: Attempt
    media_id: MediaID
    submitted_at: datetime


class TrainerAssignmentContent(BaseDTO):
    assignment: AssignmentDetail
    attachment: Optional[AssignmentAttachment] = None


class TraineeAssignmentContent(TrainerAssignmentContent):    
    submissions: list[TraineeSubmissionDetail] # His own works.



class TrainerSubmissionDetail(BaseDTO):
    id: AssignmentSubmissionID
    username: str
    email: Email
    attempt: Attempt
    max_attempt: NumberOfAttempts
    status: AssignmentSubmissionStatus
    score: Optional[Score] = None
    max_score: MaxScore
    submitted_at: datetime
    

class AssignmentSubmissionFilters(BaseDTO):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    status: Optional[AssignmentSubmissionStatus] = None
    sort_by_grade: Optional[Literal["ASC", "DESC"]] = None
    