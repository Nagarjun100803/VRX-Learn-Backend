from src.command.commands.base import BaseCmd, LessonID
from src.command.commands.lessons import (
    LessonAttachmentMetadata,
    LessonCreateCore,
    LessonUpdateCore,
)


class LessonCreateSchema(BaseCmd):
    lesson: LessonCreateCore
    attachment: LessonAttachmentMetadata


class LessonOutSchema(LessonCreateCore):
    id: LessonID


class LessonUpdateSchema(LessonUpdateCore): ...
