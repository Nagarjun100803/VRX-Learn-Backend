from src.command.commands.assignments import (
    AssignmentAttachmentMetadata,
    AssignmentCreateBase,
    AssignmentCreateCore,
    AssignmentUpdateCore,
)
from src.command.commands.base import AssignmentID, BaseCmd, CourseID


class AssignmentOut(AssignmentCreateCore):
    id: AssignmentID


class AssignmentCreateSchema(AssignmentCreateCore): ...


class AssignmentCreateWithAttachmentSchema(BaseCmd):
    course_id: CourseID
    assignment: AssignmentCreateBase
    attachment: AssignmentAttachmentMetadata


class AssignmentUpdateSchema(AssignmentUpdateCore): ...
