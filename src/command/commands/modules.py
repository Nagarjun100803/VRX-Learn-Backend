from typing import Annotated, Optional

from pydantic import ConfigDict, StringConstraints

from src.command.commands.base import (
    AuditFields,
    BaseCmd,
    CourseID,
    ModuleBase,
    ModuleID,
    NullField,
    UserID,
)
from src.command.commands.validator import UpdateValidatorMixin

ModuleTitile = Annotated[
    str, StringConstraints(to_upper=True, min_length=1, max_length=200)
]
ModuleDescription = Annotated[str, StringConstraints(max_length=5000)]


class ModuleCreateCore(BaseCmd):
    title: ModuleTitile
    description: Optional[ModuleDescription] = None
    course_id: CourseID

    model_config = ConfigDict(str_strip_whitespace=True)


class ModuleCreate(ModuleCreateCore):
    created_by: UserID


class ModuleCreateWithPosition(ModuleCreate):
    position_string: str


class ModuleUpdateCore(UpdateValidatorMixin, BaseCmd):
    title: Annotated[Optional[ModuleTitile], NullField]
    description: Annotated[Optional[ModuleDescription], NullField]

    model_config = ConfigDict(str_strip_whitespace=True)


class ModuleUpdate(ModuleUpdateCore, ModuleBase):
    updated_by: UserID


class ModuleDelete(ModuleBase):
    deleted_by: UserID


class ModuleGet(ModuleBase): ...


class ModuleGetQuery(ModuleBase):
    viewer_id: UserID


class Module(AuditFields, ModuleCreateCore, ModuleBase): ...


class ModuleReorderParticipantsCore(UpdateValidatorMixin, BaseCmd):
    preceding_id: Annotated[Optional[ModuleID], NullField]
    succeeding_id: Annotated[Optional[ModuleID], NullField]


class ModuleReorderParticipants(ModuleReorderParticipantsCore):
    target_id: ModuleID
    updated_by: UserID
