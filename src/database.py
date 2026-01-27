import contextlib
from typing import Literal, AsyncGenerator, Union, overload
import asyncpg
from asyncpg.protocol.record import Record
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from src.settings import settings
from src.query_builder.asyncpg import AsyncPgQueryBuilder
from src.query_builder.base import BaseExecutableSQL, BaseQueryBuilder



class AsyncPgDBManager:
    
    def __init__(self, query_builder: BaseQueryBuilder = AsyncPgQueryBuilder()):
        self._pool: Union[Pool, None] = None 
        self.query_builder: BaseQueryBuilder = query_builder 
    
    
    async def init_pool(self) -> None:
        
        if self._pool is not None:
            return 
        
        try:
            pool: Pool = await asyncpg.create_pool(
                user=settings.user, password=settings.password, 
                host=settings.host, database=settings.name,
                port=settings.port,
                min_size=10,
                max_size=20,
                # Senior Tip: Retire connections before they "rot"
                max_inactive_connection_lifetime=300.0, # 5 minutes
                max_queries=1000, # Recycle after 1000 uses
                command_timeout=30.0, # Don't let a single query hang your app,
            )

            self._pool = pool
            print("Database connection pool created.")
        except Exception as e:
            print(f"Error occured while creating the pool. {str(e)}")


    async def close_pool(self) -> None:
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
                print("Database connection pool closed.")
        except Exception as e:
            print(f"Error occured while closing the pool. {str(e)}")
            
    
    @contextlib.asynccontextmanager
    async def connection(self) -> AsyncGenerator[Connection, None]:
        if self._pool is None:
            raise ValueError("Initialize the pool to get connection object.")
        async with self._pool.acquire() as conn:
            yield conn 
        
        
    @overload
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["one"]
    ) -> Union[Record | None]: ...
            
    
    @overload
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["all"]
    ) -> list[Record]: ...
        
    
    @overload
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["none"]
    ) -> None: ...   
    
    
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["all", "one", "none"]
    ) -> Union[list[Record], Record, None]:
        
        print(executable.preview())
        print('==='*30)
        
        
        async with self.connection() as conn:

            if fetch_returns == "all":
                result: list[Record] = await conn.fetch(executable.sql, *executable.values)
            elif fetch_returns == "one":
                result: Union[Record | None] = await conn.fetchrow(executable.sql, *executable.values)
            else:
                result: str = await conn.execute(executable.sql, *executable.values)
            
            return result
        
    
    
    async def with_transaction(
        self,
        executables: list[BaseExecutableSQL],
        return_last: bool = True,
    ) -> Union[list[Record], Record, None]:
        
        
        if not executables:
            return None
        
        async with self.connection() as conn:
            async with conn.transaction():
                for idx, executable in enumerate(executables, start=1):
                    if idx != len(executables):
                        await conn.execute(executable.sql, *executable.values)
                    else:
                        result = await conn.fetchrow(executable.sql, *executable.values)
    
        return result if return_last else None
                    
    

async_db_manager = AsyncPgDBManager()