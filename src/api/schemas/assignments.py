from pydantic import BaseModel
from src.commands.base import AssignmentID
from src.commands.assignments import AssignmentCreateCore, AssignmentUpdateCore
from src.service.files import FileMetadata


class AssignmentOut(AssignmentCreateCore):
    id: AssignmentID

class AssignmentCreateSchema(BaseModel):
    assignment: AssignmentCreateCore
    file_metadata: FileMetadata

class AssignmentUpdateSchema(AssignmentUpdateCore): ...


