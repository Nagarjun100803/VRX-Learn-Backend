from datetime import datetime
from typing import Optional

from src.command.commands.base import IssueID, MediaID, UserID
from src.command.commands.issues import (
    AllowedIssueAttachmentContentTypes,
    IssueCategory,
    IssueDescription,
    IssueStatus,
    IssueSubject,
)
from src.command.commands.users import Email, UserRole
from src.query.dto.base import BaseDTO


class IssueSubmitterDetail(BaseDTO):
    id: UserID
    username: str
    role: UserRole
    email: Email
    submitted_at: datetime


class IssueAttachment(BaseDTO):
    id: MediaID
    filename: str
    mime_type: AllowedIssueAttachmentContentTypes


class IssueDetail(BaseDTO):
    id: IssueID
    subject: IssueSubject
    category: IssueCategory
    description: Optional[IssueDescription] = None
    status: IssueStatus
    submitted_by: IssueSubmitterDetail
    media: Optional[IssueAttachment] = None
