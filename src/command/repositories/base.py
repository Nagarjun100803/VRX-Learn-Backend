from abc import abstractmethod, ABC
from datetime import UTC, datetime
from asyncpg.protocol.record import Record
from asyncpg import Connection
from pydantic import BaseModel
from typing import Any, ClassVar, Literal, Optional, Sequence
from src.database import AsyncPgDBManager
from src.query_builder.base import BaseWhere



class BaseRepository[T](ABC):
    
    """
        Base class that provides an interface and performs common database 
        operations for all repositories. Do not use this class directly.
    """
    tablename: ClassVar[str] = "Sample"
    
    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db
    

    @abstractmethod
    def _to_domain(self, row: Optional[Record]) -> Optional[T]:
        "Converts raw database record to Domain object."
        
            

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
    async def add(self, cmd: BaseModel, connection: Optional[Connection] = None) -> T:
        "Insert new record."
        executable = self.db.query_builder.build_insert(
            self.tablename, 
            cmd.model_dump(),
        )
        
        entity = await self.db.execute(executable, fetch_returns="one", connection=connection)    
        return self._to_domain(entity)
    

    @abstractmethod
    async def update(self, cmd: BaseModel, connection: Optional[Connection] = None) -> Optional[T]:
        "Update an existing record."
        
        # Add a updated_at field.
        data = cmd.model_dump(exclude_none=True, exclude={"id"}, exclude_unset=True)
        data = self._add_audit_field(data, "update")
        executable = self.db.query_builder.build_update(
            self.tablename, data, 
            where_clause=self.db.query_builder.build_where_pk(cmd.id)
        )
        
        entity = await self.db.execute(executable, fetch_returns="one", connection=connection)
        
        return self._to_domain(entity)
        
    
    
    @abstractmethod
    async def delete(self, cmd: BaseModel, connection: Optional[Connection] = None) -> Optional[T]:
        "Delete a record."
        
        data = cmd.model_dump(exclude={"id"})
        data = self._add_audit_field(data, "delete")
        executable = self.db.query_builder.build_update(
            self.tablename, data,
            where_clause=self.db.query_builder.build_where_pk(cmd.id)
        )
        
        entity = await self.db.execute(executable, fetch_returns="one", connection=connection)
        return self._to_domain(entity)
    
    
    
    async def pick(
        self,
        columns: Sequence[str] = ("*",),
        where_clause: Optional[BaseWhere] = None,
        fetch_all: bool = False,
        connection: Optional[Connection] = None,
        **filter_kwargs: dict[str, Any]
    ) -> Optional[Record]:
        
        
        if not any([where_clause, filter_kwargs]):
            raise ValueError("Requires either a BaseWhere or a Search Kwargs to filter.")
        
        criteria = where_clause
        
        if where_clause is None:
            criteria = self.db.query_builder.build_where_from_dict(filter_kwargs)
        
        executable = self.db.query_builder.build_simple_select(
            self.tablename,
            columns=columns,
            where_clause=criteria
        )    
        
        result = await self.db.execute(executable, fetch_returns="one" if not fetch_all else "all", connection=connection) 
        return result
    
    
    
    @abstractmethod
    async def get(self, query: BaseModel, connection: Optional[Connection] = None) -> Optional[T]:
        "Get a specific record by its id."
        entitiy = await self.pick(id=query.id, connection=connection)
        return self._to_domain(entitiy)
    

    async def exists_by(
        self,
        where_clause: Optional[BaseWhere] = None,
        connection: Optional[Connection] = None,
        **filter_kwargs: dict[str, Any],
    ) -> bool:
        
        executable = self.db.query_builder.build_exists(
            self.tablename,
            where_clause,
            **filter_kwargs
        )
        
        result = await self.db.execute(executable, fetch_returns="one", connection=connection)
        return result["exists"]
        

    
        





