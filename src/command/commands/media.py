from enum import StrEnum
from typing import Annotated

from pydantic import Field

from src.command.commands.base import AuditFields, BaseCmd, MediaBase, MediaID, UserID


class AllowedContentTypes(StrEnum):
    PDF = "application/pdf"
    PNG = "image/png"
    JPG = "image/jpg"
    JPEG = "image/jpeg"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOC = "application/msword"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    PPT = "application/vnd.ms-powerpoint"
    MP4 = "video/mp4"


class MediableType(StrEnum):
    LESSON = "lesson"
    ASSIGNMENT = "assignment"
    ASSIGNMENT_SUBMISSION = "assignment-submission"
    LAB_CREDENTIAL = "lab-credential"


class MediaStatus(StrEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"


class MediaCreateCore(BaseCmd):
    filename: str
    mime_type: AllowedContentTypes
    file_size: Annotated[int, Field(gt=0, examples=[1024])]
    mediable_id: int
    mediable_type: MediableType
    is_private: bool = True
    status: MediaStatus = MediaStatus.PENDING  # Initally it's pending.
    key: str  # Storage key.


class MediaCreate(MediaCreateCore):
    created_by: UserID


class MediaStatusUpdateCore(BaseCmd):
    status: MediaStatus


class MediaStatusUpdate(MediaStatusUpdateCore, MediaBase):
    updated_by: UserID


class MediaDeleteCore(MediaBase): ...


class MediaDelete(MediaDeleteCore, MediaBase):
    deleted_by: UserID


class MediaGet(MediaBase): ...


class Media(AuditFields, MediaCreateCore, MediaBase): ...


class MediaDetail(BaseCmd):
    """Used when sending Upload urls"""

    media_id: MediaID
    filename: str
    mime_type: AllowedContentTypes
    upload_url: str
