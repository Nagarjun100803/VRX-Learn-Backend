from typing import Optional

from src.command.commands.base import BaseCmd, LessonID, ModuleID
from src.command.commands.lessons import (
    LessonAttachmentMetadata,
    LessonCreateCore,
    LessonDescription,
    LessonTitle,
    LessonUpdateCore,
)


class LessonDetail(BaseCmd):
    title: LessonTitle
    description: Optional[LessonDescription] = None


class LessonCreateSchema(BaseCmd):
    module_id: ModuleID
    lesson: LessonDetail
    attachment: LessonAttachmentMetadata


class LessonOutSchema(LessonCreateCore):
    id: LessonID


class LessonUpdateSchema(LessonUpdateCore): ...
