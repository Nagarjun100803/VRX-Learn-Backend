from pydantic import BaseModel
from src.commands.base import CourseID, ModuleID
from src.commands.modules import ModuleCreateCore, ModuleUpdateCore, ModuleTitile


class ModuleOutSchema(BaseModel):
    id: ModuleID
    title: ModuleTitile
    course_id: CourseID

class ModuleCreateSchema(ModuleCreateCore): ...
class ModuleUpdateSchema(ModuleUpdateCore): ...


