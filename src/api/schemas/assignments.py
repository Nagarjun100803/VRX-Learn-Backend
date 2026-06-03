from src.command.commands.assignments import (
    AssignmentAttachmentMetadata,
    AssignmentCreateCore,
    AssignmentUpdateCore,
)
from src.command.commands.base import AssignmentID, BaseCmd


class AssignmentOut(AssignmentCreateCore):
    id: AssignmentID


class AssignmentCreateSchema(AssignmentCreateCore): ...


class AssignmentCreateWithAttachmentSchema(BaseCmd):
    assignment: AssignmentCreateCore
    attachment: AssignmentAttachmentMetadata


class AssignmentUpdateSchema(AssignmentUpdateCore): ...
