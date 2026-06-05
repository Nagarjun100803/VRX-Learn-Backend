from src.command.commands.base import BaseCmd, IssueBase
from src.command.commands.issues import (
    IssueAttachmentMetadata,
    IssueCreateCore,
    IssueStatus,
)


class IssueOutSchema(IssueCreateCore, IssueBase):
    status: IssueStatus


class IssueCreateSchema(IssueCreateCore): ...


class IssueCreateWithAttachmentSchema(BaseCmd):
    issue: IssueCreateCore
    attachment: IssueAttachmentMetadata
