from typing import Annotated, Optional

from pydantic import StringConstraints

from src.command.commands.base import AuditFields, BaseCmd, LessonBase, LessonID, MediaID,  ModuleID, NullField, UserID
from src.command.commands.validator import UpdateValidatorMixin


LessonTitle = Annotated[str, StringConstraints(min_length=5,  max_length=256, strip_whitespace=True, to_upper=True)]


class LessonCreateCore(BaseCmd):
    title: LessonTitle
    module_id: ModuleID
    

class LessonCreate(LessonCreateCore):
    created_by: UserID
    

class LessonCreateWithPosition(LessonCreate):
    position_string: str


class LessonTitleUpdateCore(BaseCmd):
    title: LessonTitle
    
class LessonTitleUpdate(LessonTitleUpdateCore, LessonBase):
    updated_by: UserID
    
class LessonDelete(LessonBase):
    deleted_by: UserID
    
class LessonGet(LessonBase): ...

class LessonGetQuery(LessonGet):
    viewer_id: UserID

class Lesson(AuditFields, LessonCreateCore, LessonBase): ...


class LessonReArrangeCore(UpdateValidatorMixin, BaseCmd):
    preceding_id: Annotated[Optional[LessonID], NullField]
    succeeding_id: Annotated[Optional[LessonID], NullField]

class LessonReArrange(LessonReArrangeCore):
    target_id: LessonID
    updated_by: UserID
    

class LessonUploadUrl(BaseCmd):
    media_id: MediaID
    lesson_id: LessonID
    upload_url: str
    