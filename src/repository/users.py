import asyncio
from dataclasses import dataclass
from typing import ClassVar, Optional, Union, override
from asyncpg import Connection
from asyncpg.protocol.record import Record
from src.commands.users import UserCreate, UserDelete, UserGetByEmail, UserGetByID, PasswordUpdate, User
from src.repository.base import BaseRepository



@dataclass(kw_only=True)
class UserRespository(BaseRepository[User]):
    
    tablename: ClassVar[str] = "users"
    
    
    @override
    def _to_domain(self, row: Optional[Record]) -> Optional[User]:
        if not row:
            return None
        return User(**dict(row))
    
    
    async def add(self, cmd: UserCreate, connection: Optional[Connection] = None) -> User:
        return await super().add(cmd, connection)
        

    @override
    async def update(self, cmd: PasswordUpdate, connection: Optional[Connection] = None) -> Optional[User]:
                
        executable = self.db.query_builder.build_update(
            self.tablename,
            self._add_audit_field({"password": cmd.new_password}, "update"),
            where_clause=self.db.query_builder.build_where(
                column="email", value=cmd.email
            )
        )
        
        user = await self.db.execute(executable, fetch_returns="one", connection=connection)
        
        return self._to_domain(user)
        
    
    @override
    async def delete(self, cmd: UserDelete, connection: Optional[Connection] = None) -> Optional[User]:
        
        # Soft delete from all linked tables.
        data = cmd.model_dump(exclude="id")
        data = self._add_audit_field(data, "delete")
        
        # Where clause associated with user id.
        where_clause = self.db.query_builder.build_where(
            column="user_id", value=cmd.id
        )
        
        executables = [
            # Delete the enrollement first.
            # self.db.query_builder.build_update(
            #     "enrollments", data,
            #     where_clause=where_clause
            # ),
            
            # Delete the profile.
            # self.db.query_builder.build_update(
            #     "profiles", data,
            #     where_clause=where_clause
            # ),
            
            self.db.query_builder.build_update(
                self.tablename, data,
                where_clause=self.db.query_builder.build_where_pk(cmd.id)
            )    
        ] 
        
        for executable in executables:
            print(executable.preview())
            print("=="*10)
            print("\n")
            
        user = await self.db.soft_delete(executables, return_last=True, connection=connection)
        
        return self._to_domain(user)
    
    
    @override
    async def get(self, query: Union[UserGetByID, UserGetByEmail], connection: Optional[Connection] = None) -> Optional[User]:
        
        if isinstance(query, UserGetByID):
            return await super().get(query)
        
        executable = self.db.query_builder.build_simple_select(
            self.tablename,
            where_clause=self.db.query_builder.build_where(
                column="email", value=query.email
            )
        )
        
        user = await self.db.execute(executable, fetch_returns="one", connection=connection)

        return self._to_domain(user)
    
