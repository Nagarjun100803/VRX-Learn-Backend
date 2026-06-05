from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional, Self

from pydantic import StringConstraints, model_validator

from src.command.commands.base import (
    AuditFields,
    BaseAttachmentMetadata,
    BaseCmd,
    IssueBase,
    IssueID,
    MediaID,
    UserID,
)
from src.exceptions import FileSizeExceededError


class IssueCategory(StrEnum):
    ACCOUNT_ACCESS = "account-access"
    ASSIGNMENT = "assignment"
    BUG = "bug"
    COURSE_CONTENT = "course-content"
    OTHER = "other"


class IssueStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"


type IssueSubject = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
type IssueDescription = Annotated[str, StringConstraints(max_length=5000)]


class IssueCreateCore(BaseCmd):
    subject: IssueSubject
    category: IssueCategory
    description: Optional[IssueDescription] = None


class IssueCreate(IssueCreateCore):
    status: IssueStatus = IssueStatus.PENDING
    created_by: UserID


class AllowedIssueAttachmentContentTypes(StrEnum):
    PDF = "application/pdf"
    PNG = "image/png"
    JPG = "image/jpg"
    JPEG = "image/jpeg"


MAX_BYTES = 5 * 1024 * 1024


class IssueAttachmentMetadata(
    BaseAttachmentMetadata[AllowedIssueAttachmentContentTypes]
):
    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.size > MAX_BYTES:
            raise FileSizeExceededError(max_size=MAX_BYTES)
        return self


class IssueAttachmentUploadContext(IssueCreate):
    id: IssueID
    created_at: datetime
    media_id: MediaID
    url: str


class IssueDetail(IssueCreate, IssueBase):
    created_at: datetime


class IssueStatusUpdateCore(BaseCmd):
    status: IssueStatus


class IssueAttachmentStatusUpdate(IssueBase):
    updated_by: UserID


class IssueStatusUpdate(IssueStatusUpdateCore):
    id: IssueID
    updated_by: UserID


class IssueGet(IssueBase):
    viewer_id: UserID


class Issue(AuditFields, IssueCreateCore, IssueBase):
    status: IssueStatus
