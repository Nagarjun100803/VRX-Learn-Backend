from asyncpg import Connection, Record
from src.repository.base import BaseRepository
from src.repository.ownership_specification import BaseOwnershipSpec, EnrollmentOwnershipSpec
from dataclasses import dataclass
from typing import ClassVar, Type, Optional
from src.commands.enrollments import (
        Enrollment, EnrollmentCreate, EnrollmentUpdate, 
        EnrollmentDelete, EnrollmentGet
)


@dataclass(kw_only=True)
class EnrollmentRepository(BaseRepository[Enrollment]):
   
    tablename: ClassVar[str] = "enrollments"
    _ownership_spec: ClassVar[Type[BaseOwnershipSpec]] = EnrollmentOwnershipSpec
    
    
    def _to_domain(self, row: Optional[Record]) -> Optional[Enrollment]:
        if row is None:
            return None
        return Enrollment(**row)
    
    
    async def add(
        self, 
        cmd: EnrollmentCreate, 
        connection: Optional[Connection] = None
    ):
        return await super().add(cmd, connection)
    
    
    async def update(
        self, 
        cmd: EnrollmentUpdate, 
        connection: Optional[Connection] = None
        
    ):
        return await super().update(cmd, connection)
    
    
    async def delete(
        self, 
        cmd: EnrollmentDelete, 
        connection: Optional[Connection] = None
    ):
        return await super().delete(cmd, connection)
    
    
    async def get(
        self, 
        query: EnrollmentGet, 
        connection: Optional[Connection] = None
    ):
        return await super().get(query, connection)