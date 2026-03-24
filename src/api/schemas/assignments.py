from typing import Optional

from src.command.commands.base import AssignmentID, BaseCmd
from src.command.commands.assignments import AssignmentCreateCore, AssignmentUpdateCore
from src.command.services.files import FileMetadata


class AssignmentOut(AssignmentCreateCore):
    id: AssignmentID

class AssignmentCreateSchema(BaseCmd):
    assignment: AssignmentCreateCore
    file_metadata: Optional[FileMetadata]

class AssignmentUpdateSchema(AssignmentUpdateCore): ...


