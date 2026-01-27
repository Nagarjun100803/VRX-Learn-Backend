from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence, Union
from src.commands.base import AnyID



class BaseExecutableSQL(ABC): 
    
    sql: str
    values: tuple
        
    @abstractmethod
    def preview(self) -> str: ...



class BaseWhere(ABC): 
    condition: str
    values: dict[str, Any]


class BaseQueryBuilder(ABC):
    
    @abstractmethod
    def build_insert(
        self,
        tablename: str,
        data: dict[str, Any],
        return_columns: Sequence[str] = ("*", )
    ) -> BaseExecutableSQL: ...
    
    
    @abstractmethod
    def build_update(
        self,
        tablename: str,
        data: dict[str, Any],
        where_clause: Optional[BaseWhere] = None,
        return_columns: Sequence[str] = ("*", )
    ) -> BaseExecutableSQL: ...
    

    @abstractmethod
    def build_simple_select(
        self,
        tablename: str,
        columns: Sequence[str] = ("*", ),
        where_clause: Optional[BaseWhere] = None
    ) -> BaseExecutableSQL: ...
    

    
    @abstractmethod
    def build_where(
        self,
        value: Union[str, int],
        column: str = "id",
    ) -> BaseWhere: ...
    
    
    def build_where_pk(
        self,
        value: AnyID
    ) -> BaseWhere: ...
    
    
    def build_base_where(
        self,
        condition: str,
        values: dict
    ) -> BaseWhere: ...
    
   
    def build_executable(
       self,
       sql: str,
       values: tuple
    ) -> BaseExecutableSQL:
        ...
    
    