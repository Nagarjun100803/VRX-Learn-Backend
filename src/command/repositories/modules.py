from asyncpg import Record, Connection
from typing import ClassVar, Optional, override
from src.command.repositories.base import BaseRepository
from src.command.commands.modules import Module, ModuleCreateWithPosition, ModuleDelete, ModuleGetQuery, ModuleUpdate
from src.command.commands.media import MediableType


class ModuleRepository(BaseRepository[Module]):
    
    tablename: ClassVar[str] = "modules"

    
    @override
    def _to_domain(self, row: Optional[Record]):
        if row is None:
            return None
        return Module(**row)
        
    
    async def add(self, cmd: ModuleCreateWithPosition, connection: Optional[Connection] = None) -> Module:
        return await super().add(cmd, connection=connection)
    
    
    async def update(self, cmd: ModuleUpdate, connection: Optional[Connection] = None) -> Optional[Module]:
        return await super().update(cmd, connection=connection)
    
    
    @override
    async def delete(self, cmd: ModuleDelete, connection: Optional[Connection] = None) -> Optional[Module]:
        # Unlink the relationships.
        data = cmd.model_dump(exclude={"id"})
        data = self._add_audit_field(data, action="delete")
        print(f"Delete payload is {data}")
        
        executables = [
            # If necessary we can unlink the connections.
            self.db.query_builder.build_update(
                "media_assets", data,
                where_clause=self.db.query_builder.build_base_where(
                    condition="""
                        Where 
                            mediable_type = ($mediable_type) and 
                            mediable_id In (
                                select 
                                    id
                                from 
                                    lessons as l
                                where
                                    l.module_id = ($module_id) and 
                                    l.deleted_at is Null
                            ) and
                            deleted_at is Null 
                    """,
                    values={
                        "mediable_type": MediableType.LESSON,
                        "module_id": cmd.id
                    }
                )
                
            ),
            self.db.query_builder.build_update(
                "lessons", data,
                where_clause=self.db.query_builder.build_base_where(
                    condition="Where module_id = ($module_id) and deleted_at is Null",
                    values={"module_id": cmd.id}
                )
            ),
            self.db.query_builder.build_update(
                self.tablename, data,
                where_clause=self.db.query_builder.build_where_pk(cmd.id)
            )
   
        ]
        module = await self.db.soft_delete(executables, return_last=True, connection=connection)
        return self._to_domain(module)
                
                
    async def get(self, query: ModuleGetQuery, connection: Optional[Connection] = None) -> Optional[Module]:
        return await super().get(query, connection=connection)
    



