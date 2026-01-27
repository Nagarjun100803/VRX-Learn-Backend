from abc import abstractmethod, ABC
from datetime import UTC, datetime
from asyncpg.protocol.record import Record
from pydantic import BaseModel
from typing import Any, ClassVar, Literal, Optional, Type, Union
from src.database import AsyncPgDBManager, async_db_manager
from src.commands.base import UserID, ID
from src.query_builder.base import BaseWhere
from src.query_builder.asyncpg import AsyncPgWhere
from src.repository.ownership_specification import BaseOwnershipSpec
import asyncio


class BaseRepository[T](ABC):
    
    """
        Base class that provides an interface and performs common database 
        operations for all repositories. Do not use this class directly.
    """
    
    tablename: ClassVar[str] = "Sample"
    _ownership_spec: ClassVar[Type[BaseOwnershipSpec]]
    
    
    def __init__(self, db: Optional[AsyncPgDBManager] = None) -> None:
        super().__init__()
        self.db = db or async_db_manager


    @abstractmethod
    def _to_domain(self, row: Optional[Record]) -> Optional[T]:
        "Converts raw database record to Domain object."
        
    
    async def verify_ownership(
        self,
        entity_id: ID,
        user_id: UserID,
    ) -> bool:
        
        spec = self._ownership_spec(entity_id, user_id)
        return await spec.is_satisfied()
        

    def _add_audit_field(
        self,
        data: dict[str, Any], 
        action: Literal["update", "delete"]
    ) -> dict[str, Any]:
        
        allowded_actions = {"update", "delete"}
        if action not in allowded_actions:
            raise ValueError(f"Invalid action '{action}'. Allowded actions are '{allowded_actions}'")
        
        current_timstamptz = datetime.now(tz=UTC)
        updated_dict = data.copy()        
        to_update_key = "updated_at" if action == "update" else "deleted_at" 
        updated_dict.update({to_update_key: current_timstamptz})
        return updated_dict
    
    
    @abstractmethod
    async def add(self, cmd: BaseModel) -> T:
        "Insert new record."
        executable = self.db.query_builder.build_insert(
            self.tablename, 
            cmd.model_dump(),
        )
        
        entity = await self.db.execute(executable, fetch_returns="one")    
        return self._to_domain(entity)
    

    @abstractmethod
    async def update(self, cmd: BaseModel) -> Optional[T]:
        "Update an existing record."
        
        # Add a updated_at field.
        data = cmd.model_dump(exclude_none=True, exclude={"id"}, exclude_unset=True)
        data = self._add_audit_field(data, "update")
        executable = self.db.query_builder.build_update(
            self.tablename, data, 
            where_clause=self.db.query_builder.build_where_pk(cmd.id)
        )
        
        entity = await self.db.execute(executable, fetch_returns="one")
        
        return self._to_domain(entity)
        
    
    
    @abstractmethod
    async def delete(self, cmd: BaseModel) -> Optional[T]:
        "Delete a record."
        
        data = cmd.model_dump(exclude={"id"})
        data = self._add_audit_field(data, "delete")
        executable = self.db.query_builder.build_update(
            self.tablename, data,
            where_clause=self.db.query_builder.build_where_pk(cmd.id)
        )
        
        entity = await self.db.execute(executable, fetch_returns="one")
        return self._to_domain(entity)
    
    
    # async def _lookup(
    #     self, 
    #     criteria: str, 
    #     value: Union[int, str], 
    #     return_type: Literal["bool", "record"]
    # ) -> Optional[Record]:
    #     """
    #         Helper function used to lookup for a specific
    #         record and return raw database row.
    #     """
    #     if criteria not in self._lookup_criteria:
    #         raise ValueError(f"Invalid criteria '{criteria}', Allowded criterias are {self._lookup_criteria}")
        
    #     columns = ["*"] if return_type == "record" else ["1"]
    #     where_clause = self.db.query_builder.build_where(
    #         column=criteria, value=value
    #     )
        
    #     executable = self.db.query_builder.build_simple_select(self.tablename, columns, where_clause)
        
    #     entity = await self.db.execute(executable, fetch_returns="one")
        
    #     return entity
    
        
    # @abstractmethod
    # async def get(self, query: BaseModel) -> Optional[T]:
    #     "Get a specific record by it's id."
    #     entity = await self._lookup(criteria="id", value=query.id, return_type="record")
    #     return self._to_domain(entity)
    
    
    # @abstractmethod
    # async def exists_by(
    #     self, 
    #     criteria: str, 
    #     value: Union[str, int],
    #     **scope_kwargs: dict[str, Any]
    # ) -> bool:
    #     "Check a record is exist with specific criteria."
    #     entity: Optional[Record] = await self._lookup(criteria, value, return_type="bool")
    #     return bool(entity)
    
    
    @abstractmethod
    async def get(self, query: BaseModel):
        "Get a specific record by its id."
        executable = self.db.query_builder.build_simple_select(
            self.tablename,
            where_clause=self.db.query_builder.build_where_pk(query.id)
        )
        print(executable.preview())
        entity = await self.db.execute(executable, fetch_returns="one")
        return self._to_domain(entity)
    
    
    
    async def exists_by(
        self,
        where_clause: Optional[BaseWhere] = None,
        **search_kwargs: dict[str, Any],
    ) -> bool:
        
        
        # By default it only only supports for And operator.
        # If we want, we can pass the condition as BaseWhere.
        
        if not any([where_clause, search_kwargs]):
            raise ValueError("Requires either a BaseWhere or a Search Kwargs to filter.")
        
        critera = where_clause
        
        if where_clause is None:
            where_clause_condition = "Where "
            where_clause_condition += " and ".join([f'{col}=(${col})' for col in search_kwargs.keys()])
            where_clause_condition += "and deleted_at is null"
            critera = AsyncPgWhere(condition=where_clause_condition, values=search_kwargs)
        
        executable = self.db.query_builder.build_simple_select(
            self.tablename,
            columns=("1",),
            where_clause= critera
        )    
                
        result = await self.db.execute(executable, fetch_returns="one")
        return bool(result)
    
        

        
        
        
        




