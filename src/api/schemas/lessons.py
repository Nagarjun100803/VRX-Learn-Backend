from pathlib import Path
from typing import Annotated, Union

from pydantic import Field

from src.command.commands.base import LessonID
from src.command.commands.lessons import LessonCreateCore, LessonTitleUpdateCore
from src.command.commands.media import AllowedContentTypes


class LessonCreateSchema(LessonCreateCore):
    filename: Union[str, Path]
    content_type: AllowedContentTypes
    file_size: Annotated[int, Field(gt=0)]
    

class LessonOutSchema(LessonCreateCore):
    id: LessonID    

class LessonTitleUpdateSchema(LessonTitleUpdateCore): ...

