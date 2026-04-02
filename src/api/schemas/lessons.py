from typing import Annotated

from pydantic import Field

from src.command.commands.base import LessonID
from src.command.commands.lessons import LessonCreateCore, LessonUpdateCore
from src.command.commands.media import AllowedContentTypes


class LessonCreateSchema(LessonCreateCore):
    filename: str
    content_type: AllowedContentTypes
    file_size: Annotated[int, Field(gt=0)]


class LessonOutSchema(LessonCreateCore):
    id: LessonID


class LessonUpdateSchema(LessonUpdateCore): ...
