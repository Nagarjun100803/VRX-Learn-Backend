from datetime import datetime
from typing import Optional

from src.command.commands.base import IssueID, MediaID, UserID
from src.command.commands.issues import (
    AllowedIssueFileType,
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
    mime_type: AllowedIssueFileType


class IssueDetail(BaseDTO):
    id: IssueID
    subject: IssueSubject
    category: IssueCategory
    description: Optional[IssueDescription] = None
    status: IssueStatus
    submitted_by: IssueSubmitterDetail
    media: Optional[IssueAttachment] = None


if __name__ == "__main__":
    issue = IssueDetail(
        id=1,
        subject="I cannot login",
        category=IssueCategory.ACCOUNT_ACCESS,
        description=None,
        status=IssueStatus.PENDING,
        submitted_by=IssueSubmitterDetail(
            id=1,
            username="nagarjun",
            role=UserRole.TRAINEE,
            email="nagarjun@gmail.com",
            submitted_at=datetime.now(),
        ),
        media=IssueAttachment(
            id=1, filename="screenshot-png", mime_type=AllowedIssueFileType.PDF
        ),
    )

    print(issue.model_dump_json(indent=4, by_alias=True))
