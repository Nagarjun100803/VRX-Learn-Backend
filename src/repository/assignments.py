from asyncpg import Record, Connection
from dataclasses import dataclass
from typing import Optional, ClassVar
from src.commands.assignments import Assignment, AssignmentCreateWithPosition, AssignmentUpdate, AssignmentDelete, AssignmentGet
from src.repository.base import BaseRepository


@dataclass(kw_only=True)
class AssignmentRepository(BaseRepository[Assignment]):
    
    tablename: ClassVar[str] = "assignments"
    
    
    def _to_domain(self, row: Optional[Record]) -> Optional[Assignment]:
        if row is None:
            return None
        return Assignment(**row)
    
        
    async def add(self, cmd: AssignmentCreateWithPosition, connection: Optional[Connection] = None) -> Assignment:
        return await super().add(cmd, connection=connection)
    
    async def update(self, cmd: AssignmentUpdate, connection: Optional[Connection] = None) -> Optional[Assignment]:
        return await super().update(cmd, connection=connection)
    
    async def delete(self, cmd: AssignmentDelete, connection: Optional[Connection] = None) -> Optional[Assignment]:
        # TODO: Need to unlink all the submitted assignments from it.
        return await super().delete(cmd, connection=connection)
    
    async def get(self, query: AssignmentGet, connection: Optional[Connection] = None) -> Optional[Assignment]:
        return await super().get(query, connection=connection)

