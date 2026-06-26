from typing import Optional

from src.command.commands.base import BaseCmd, CourseID, ModuleID
from src.command.commands.modules import (
    ModuleCreateCore,
    ModuleDescription,
    ModuleTitle,
    ModuleUpdateCore,
)


class ModuleOutSchema(BaseCmd):
    id: ModuleID
    title: ModuleTitle
    description: Optional[ModuleDescription] = None
    course_id: CourseID


class ModuleCreateSchema(ModuleCreateCore): ...


class ModuleUpdateSchema(ModuleUpdateCore): ...
