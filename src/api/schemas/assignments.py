from typing import Optional, Annotated
from pydantic import BaseModel
from src.command.commands.base import AssignmentID
from src.command.commands.assignments import AssignmentCreateCore, AssignmentUpdateCore
from src.command.services.files import FileMetadata


class AssignmentOut(AssignmentCreateCore):
    id: AssignmentID

class AssignmentCreateSchema(BaseModel):
    assignment: AssignmentCreateCore
    file_metadata: Optional[FileMetadata]

class AssignmentUpdateSchema(AssignmentUpdateCore): ...


