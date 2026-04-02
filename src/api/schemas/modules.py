from src.command.commands.base import BaseCmd, CourseID, ModuleID
from src.command.commands.modules import (
    ModuleCreateCore,
    ModuleTitile,
    ModuleUpdateCore,
)


class ModuleOutSchema(BaseCmd):
    id: ModuleID
    title: ModuleTitile
    course_id: CourseID


class ModuleCreateSchema(ModuleCreateCore): ...


class ModuleUpdateSchema(ModuleUpdateCore): ...
