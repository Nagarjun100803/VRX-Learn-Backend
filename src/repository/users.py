import asyncio
from typing import ClassVar, Optional, Union, Literal, override
from asyncpg.protocol.record import Record
from src.commands.users import UserCreate, UserDelete, UserGetByEmail, UserGetByID, PasswordUpdate, User
from src.query_builder.asyncpg import AsyncPgWhere
from src.repository.base import BaseRepository
from src.repository.ownership_specification import BaseOwnershipSpec, UserOwnershipSpec




class UserRespository(BaseRepository[User]):
    
    tablename: ClassVar[str] = "users"
    _ownership_spec: ClassVar[BaseOwnershipSpec] = UserOwnershipSpec
    
    
    @override
    def _to_domain(self, row: Optional[Record]) -> Optional[User]:
        if not row:
            return None
        return User(**dict(row))
    
    
    async def add(self, cmd: UserCreate) -> User:
        return await super().add(cmd)
        

    @override
    async def update(self, cmd: PasswordUpdate) -> Optional[User]:
                
        executable = self.db.query_builder.build_update(
            self.tablename,
            self._add_audit_field({"password": cmd.new_password}, "update"),
            where_clause=self.db.query_builder.build_where(
                column="email", value=cmd.email
            )
        )
        
        user = await self.db.execute(executable, fetch_returns="one")
        
        return self._to_domain(user)
        
    
    @override
    async def delete(self, cmd: UserDelete) -> Optional[User]:
        
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
            
        user = await self.db.with_transaction(executables)
        
        return self._to_domain(user)
    
    
    @override
    async def get(self, query: Union[UserGetByID, UserGetByEmail]) -> Optional[User]:
        
        if isinstance(query, UserGetByID):
            return await super().get(query)
        
        executable = self.db.query_builder.build_simple_select(
            self.tablename,
            where_clause=self.db.query_builder.build_where(
                column="email", value=query.email
            )
        )
        
        user = await self.db.execute(executable, fetch_returns="one")

        return self._to_domain(user)
    
