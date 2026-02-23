from asyncpg import Record
from typing import Optional, ClassVar
from src.commands.assignments import Assignment, AssignmentCreateWithPosition, AssignmentUpdate, AssignmentDelete, AssignmentGet
from src.repository.base import BaseRepository
from src.repository.ownership_specification import BaseOwnershipSpec, AssignmentOwnershipSpec


class AssignmentRepository(BaseRepository[Assignment]):
    
    tablename: ClassVar[str] = "assignments"
    _ownership_spec: ClassVar[BaseOwnershipSpec] = AssignmentOwnershipSpec
    
    
    def _to_domain(self, row: Optional[Record]) -> Optional[Assignment]:
        if row is None:
            return None
        return Assignment(**row)
    
        
    async def add(self, cmd: AssignmentCreateWithPosition) -> Assignment:
        return await super().add(cmd)
    
    async def update(self, cmd: AssignmentUpdate) -> Optional[Assignment]:
        return await super().update(cmd)
    
    async def delete(self, cmd: AssignmentDelete) -> Optional[Assignment]:
        # TODO: Need to unlink all the submitted assignments from it.
        return await super().delete(cmd)
    
    async def get(self, query: AssignmentGet) -> Optional[Assignment]:
        return await super().get(query)

