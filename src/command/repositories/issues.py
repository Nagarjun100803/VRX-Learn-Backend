from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel

from src.command.commands.issues import Issue, IssueBase, IssueCreate, IssueStatusUpdate
from src.command.repositories.base import BaseRepository


class IssueRepository(BaseRepository[Issue]):
    tablename: ClassVar[str] = "issues"

    def _to_domain(self, row: Optional[Record]) -> Optional[Issue]:
        if row is not None:
            return Issue.model_validate(dict(row))
        return row

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Issue:
        cmd = self._normalize(cmd=cmd, model=IssueCreate)
        return await super().add(cmd, connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Issue]:
        cmd = self._normalize(cmd=cmd, model=IssueStatusUpdate)
        return await super().update(cmd, connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Issue]:
        query = self._normalize(cmd=query, model=IssueBase)
        return await super().get(query, connection)

    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Issue]:

        raise NotImplementedError()
