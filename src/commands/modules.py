from datetime import datetime
from pydantic import BaseModel, StringConstraints, ConfigDict
from typing import Annotated, Optional
from src.commands.base import ModuleBase, CourseID, UserID, NullField
from src.commands.validator import UpdateValidatorMixin



ModuleTitile = Annotated[str, StringConstraints(to_upper=True)]
ModuleDescription = Annotated[str, StringConstraints(min_length=20)]



class ModuleCreateCore(BaseModel):
    title: ModuleTitile
    description: ModuleDescription
    course_id: CourseID

    model_config = ConfigDict(str_strip_whitespace=True)  
    
    

class ModuleCreate(ModuleCreateCore):
    created_by: UserID
    

class ModuleUpdateCore(UpdateValidatorMixin, BaseModel):
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


class Module(ModuleBase, ModuleCreate):
    created_at: datetime
    deleted_at: Optional[datetime] = None