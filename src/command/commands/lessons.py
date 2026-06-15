from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional, Self

from pydantic import StringConstraints, model_validator

from src.command.commands.base import (
    BaseAttachmentMetadata,
    BaseCmd,
    DeleteAuditField,
    LessonBase,
    LessonID,
    MediaID,
    ModuleID,
    NullField,
    UpdateAuditFields,
    UserID,
)
from src.command.commands.media import AllowedContentTypes
from src.command.commands.validator import UpdateValidatorMixin
from src.exceptions import FileSizeExceededError

type LessonTitle = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=200, strip_whitespace=True, to_upper=True
    ),
]
type LessonDescription = Annotated[str, StringConstraints(max_length=5000)]


class AllowedLessonAttachmentContentTypes(StrEnum):
    PDF = "application/pdf"
    MP4 = "video/mp4"


MAX_BYTES = int(2.5 * 1024 * 1024 * 1024)


class LessonAttachmentMetadata(
    BaseAttachmentMetadata[AllowedLessonAttachmentContentTypes]
):
    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.size > MAX_BYTES:
            raise FileSizeExceededError(max_size=MAX_BYTES)
        return self


class LessonCreateCore(BaseCmd):
    title: LessonTitle
    description: Optional[LessonDescription] = None
    module_id: ModuleID


class LessonCreate(LessonCreateCore):
    created_by: UserID


class LessonCreateWithPosition(LessonCreate):
    position_string: str


class LessonContext(LessonCreate):
    id: LessonID


class LessonUpdateCore(UpdateValidatorMixin, BaseCmd):
    title: Annotated[Optional[LessonTitle], NullField]
    description: Annotated[Optional[LessonDescription], NullField]


class LessonUpdate(LessonUpdateCore, LessonBase):
    updated_by: UserID


class LessonAttachmentStatusUpdate(LessonBase):
    updated_by: UserID


class LessonDelete(LessonBase):
    deleted_by: UserID


class LessonGet(LessonBase): ...


class LessonGetQuery(LessonGet):
    viewer_id: UserID


class Lesson(DeleteAuditField, UpdateAuditFields, LessonCreateCore, LessonBase):
    created_by: UserID
    created_at: datetime


class LessonReorderParticipantsCore(UpdateValidatorMixin, BaseCmd):
    preceding_id: Annotated[Optional[LessonID], NullField]
    succeeding_id: Annotated[Optional[LessonID], NullField]


class LessonReorderParticipants(LessonReorderParticipantsCore):
    target_id: LessonID
    updated_by: UserID


class LessonWithMedia(BaseCmd):
    id: LessonID
    title: LessonTitle
    description: Optional[LessonDescription] = None
    media_id: MediaID
    mime_type: AllowedContentTypes
