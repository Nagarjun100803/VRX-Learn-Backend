from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional

from pydantic import StringConstraints

from src.command.commands.base import AuditFields, BaseCmd, IssueBase, IssueID, UserID
from src.command.commands.media import MediaDetail


class AllowedIssueFileType(StrEnum):
    PDF = "application/pdf"
    JPEG = "image/jpeg"
    JPG = "image/jpg"
    PNG = "image/png"


class IssueCategory(StrEnum):
    ACCOUNT_ACCESS = "account-access"
    ASSIGNMENT = "assignment"
    BUG = "bug"
    COURSE_CONTENT = "course-content"
    OTHER = "other"


class IssueStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"


type IssueSubject = Annotated[str, StringConstraints(min_length=10, max_length=100)]
type IssueDescription = Annotated[str, StringConstraints(max_length=2000)]


class IssueCreateCore(BaseCmd):
    subject: IssueSubject
    category: IssueCategory
    description: Optional[IssueDescription] = None


class IssueCreate(IssueCreateCore):
    status: IssueStatus = IssueStatus.PENDING
    created_by: UserID


class IssueDetail(IssueCreate, IssueBase):
    created_at: datetime


class IssueUpload(BaseCmd):
    issue: IssueDetail
    media: MediaDetail


class IssueStatusUpdateCore(BaseCmd):
    status: IssueStatus


class IssueStatusUpdate(IssueStatusUpdateCore):
    id: IssueID
    updated_by: UserID


class IssueGet(IssueBase):
    viewer_id: UserID


class Issue(AuditFields, IssueCreateCore, IssueBase):
    status: IssueStatus
