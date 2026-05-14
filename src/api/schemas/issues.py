from typing import Optional

from src.command.commands.base import BaseCmd, IssueBase
from src.command.commands.issues import IssueCreateCore, IssueStatus
from src.command.services.files import FileMetadata


class IssueOutSchema(IssueCreateCore, IssueBase):
    status: IssueStatus


class IssueCreateSchema(BaseCmd):
    issue: IssueCreateCore
    file_metadata: Optional[FileMetadata]
