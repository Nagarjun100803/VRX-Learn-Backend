from asyncpg import Connection, Record
from src.command.repositories.base import BaseRepository
from typing import ClassVar, Optional
from src.command.commands.enrollments import (
        Enrollment, EnrollmentCreate, EnrollmentUpdate, 
        EnrollmentDelete, EnrollmentGet
)


class EnrollmentRepository(BaseRepository[Enrollment]):
   
    tablename: ClassVar[str] = "enrollments"
    
    
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