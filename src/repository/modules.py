from asyncpg.protocol.record import Record
from typing import Any, ClassVar, Literal, Optional, Type, Union, overload, override
from src.query_builder.asyncpg import AsyncPgExecutableSQL
from src.repository.base import BaseRepository
from src.commands.base import EntityBase, ModuleBase, ModuleID, UserID
from src.commands.modules import Module, ModuleCreate, ModuleDelete, ModuleGetQuery, ModuleUpdate
from src.repository.ownership_specification import BaseOwnershipSpec, ModuleOwnershipSpec
import asyncio


class ModuleRepository(BaseRepository[Module]):
    
    tablename: ClassVar[str] = "modules"
    _ownership_spec: ClassVar[Type[BaseOwnershipSpec]] = ModuleOwnershipSpec

    
    @override
    def _to_domain(self, row: Optional[Record]):
        if row is None:
            return None
        return Module(**row)
        
    
    async def add(self, cmd: ModuleCreate) -> Module:
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
    




async def main():
    
    repo = ModuleRepository()
    await repo.db.init_pool()
    
    # module = ModuleCreate(
    #     title="Module 1",
    #     description="This is sample " * 10,
    #     course_id=4,
    #     created_by=1
    # ) 
    # new_module = await repo.add(module)
    # module = await repo.get(ModuleGetQuery(id="M-1", viewer_id=1))
    # module = await repo.exists_by("title", "module 1".upper())
    # module = await repo.exists_by("id", 1)
    # module = await repo.delete(ModuleDelete(id=1, deleted_by="U-1"))
    # module = await repo.update(ModuleUpdate(id=1, title="Updated title 2", description="Module Description " * 10  ,updated_by=1))
    # print(module)
    ow = await repo.verify_ownership(1, 3)
    print(ow)
    
    await repo.db.close_pool()
    

if __name__ == "__main__":
   asyncio.run(main())


