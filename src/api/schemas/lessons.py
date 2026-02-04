from pathlib import Path
from src.commands.base import LessonID
from src.commands.lessons import LessonCreateCore, LessonTitleUpdateCore, LessonReArrangeCore
from pydantic import Field
from typing import Annotated, Union
from src.commands.media import AllowedContentTypes


class LessonCreateSchema(LessonCreateCore):
    filename: Union[str, Path]
    content_type: AllowedContentTypes
    file_size: Annotated[int, Field(gt=0)]
    

class LessonOutSchema(LessonCreateCore):
    id: LessonID    

class LessonTitleUpdateSchema(LessonTitleUpdateCore): ...

class LessonReArrangeSchema(LessonReArrangeCore): ...

