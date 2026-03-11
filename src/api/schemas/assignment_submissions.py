from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.command.commands.assignment_submissions import (
    AssignmentSubmissionCreateCore,
    AssignmentSubmissionStatus, 
    AssignmentSubmissionVerifyCore,
    AssignmentSubmissionFeedbackUpdateCore,
    Score,
)
from src.command.commands.assignment_submissions import AssignmentSubmissionBase
from src.command.commands.base import AssignmentID, UserID
from src.command.services.files import FileMetadata


class AssignmentSubmissionOut(AssignmentSubmissionBase):
    assignment_id: AssignmentID
    status: AssignmentSubmissionStatus
    score: Optional[Score] = None
    created_by: UserID
    created_at: datetime
    

class AssignmentSubmissionCreateSchema(BaseModel):
    assignment_submission: AssignmentSubmissionCreateCore
    file_metadata: FileMetadata
     

class AssignmentSubmissionVerifySchema(AssignmentSubmissionVerifyCore): ...
class AssignmentSubmissionFeedbackUpdateSchema(AssignmentSubmissionFeedbackUpdateCore): ...



    
