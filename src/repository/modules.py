from asyncpg.protocol.record import Record
from typing import ClassVar, Optional, Type, override
from src.repository.base import BaseRepository
from src.commands.modules import Module, ModuleCreateWithPosition, ModuleDelete, ModuleGetQuery, ModuleUpdate, ReArrangeModule
from src.repository.ownership_specification import BaseOwnershipSpec, ModuleOwnershipSpec


class ModuleRepository(BaseRepository[Module]):
    
    tablename: ClassVar[str] = "modules"
    _ownership_spec: ClassVar[Type[BaseOwnershipSpec]] = ModuleOwnershipSpec

    
    @override
    def _to_domain(self, row: Optional[Record]):
        if row is None:
            return None
        return Module(**row)
        
    
    async def add(self, cmd: ModuleCreateWithPosition) -> Module:
        return await super().add(cmd)
    
    
    async def update(self, cmd: ModuleUpdate):
        return await super().update(cmd)
    
    
    @override
    async def delete(self, cmd: ModuleDelete):
        # Unlink the relationships.
        data = cmd.model_dump(exclude={"id"})
        data = self._add_audit_field(data, action="delete")
        print(f"Delete payload is {data}")
        
        executables = [
            
            # If necessary we can unlink the connections.
            
            # self.db.query_builder.build_update(
            #     "lessons",
            #     data,
            #     where_clause=self.db.query_builder.build_base_where(
            #         condition="Where module_id = ($module_id) and deleted_at is Null",
            #         values={"module_id": cmd.id}
            #     )
            # ),
            self.db.query_builder.build_update(
                self.tablename, data,
                where_clause=self.db.query_builder.build_where_pk(cmd.id)
            )
            
        ]
        module = await self.db.with_transaction(executables, return_last=True)
        return self._to_domain(module)
                
                
    async def get(self, query: ModuleGetQuery) -> Optional[Module]:
        return await super().get(query)
    



