import contextlib
import json
from typing import Literal, AsyncGenerator, Optional, Union, overload
import asyncpg
from asyncpg import Connection, Pool, Record
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
                user=settings.database.user.get_secret_value(), password=settings.database.password.get_secret_value(), 
                host=settings.database.host.get_secret_value(), database=settings.database.name.get_secret_value(),
                port=settings.database.port,
                min_size=10,
                max_size=100,
                # Senior Tip: Retire connections before they "rot"
                max_inactive_connection_lifetime=300.0, # 5 minutes
                max_queries=1000, # Recycle after 1000 uses
                command_timeout=30.0, # Don't let a single query hang your app,
                init=self.set_codecs
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
       
    
    @staticmethod
    async def set_codecs(connection: Connection) -> None:
        """
        Registers JSONB codecs so asyncpg can automatically 
        translate between Python dicts and Postgres jsonb.
        """

        await connection.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog"
        )     
    
    @contextlib.asynccontextmanager
    async def _get_connection(self, connection: Optional[Connection]) -> AsyncGenerator[Connection, None]:
        """
            ### Helper context manager to yield a connection.
            - Case 1: If a connection is provided, yield that connection. This is useful when 
                    we are already in a transaction and want to reuse the same connection.
                    
            - Case 2: If no connection is provided, acquire a new connection from the pool and yield it.
            
            NOTE: The connection is released back to the pool automatically when the context manager exits, even if an exception occurs. 
            This ensures that we don't leak connections.
        """
        if connection is not None:
            yield connection
            print("Reusing the provided connection.")
        else:
            async with self._pool.acquire() as connection:
                yield connection
                
            
    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """
            ### Helper context manager to manage transactions.
            This context manager can be used to wrap a block of code in a transaction. 
            It will automatically commit the transaction if the block of code executes successfully, 
            or roll back the transaction if an exception occurs.
        """
        if self._pool is None:
            raise ValueError("Initialize the pool to get connection object.")
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn
      
            
    @overload
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["one"],
        connection: Optional[Connection] = None
    ) -> Union[Record | None]: ...
            
    
    @overload
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["all"],
        connection: Optional[Connection] = None
    ) -> list[Record]: ...
        
    
    @overload
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["none"],
        connection: Optional[Connection] = None
    ) -> None: ...   
    
    
    async def execute(
        self,
        executable: BaseExecutableSQL,
        fetch_returns: Literal["all", "one", "none"],
        connection: Optional[Connection] = None
    ):
        """
            This method executes a given SQL command and returns the result based on the specified fetch mode.
            - `fetch_returns="one"`: Returns a single record as a `Record` object, or `None` if no record is found.
            - `fetch_returns="all"`: Returns a list of `Record` objects, which
            - `fetch_returns="none"`: Executes the command without returning any records (useful for INSERT, UPDATE, DELETE operations that does not use RETURNING statement).
            
        """
        print("==="*10)
        print(executable.preview())
        print("==="*10)
        
        async with self._get_connection(connection) as conn:
            if fetch_returns == "all":
                result: list[Record] = await conn.fetch(executable.sql, *executable.values)
            elif fetch_returns == "one":
                result: Union[Record | None] = await conn.fetchrow(executable.sql, *executable.values)
            else:
                result: str = await conn.execute(executable.sql, *executable.values)
            
            return result
    
    
    async def soft_delete(
        self,
        executables: list[BaseExecutableSQL],
        return_last: bool = True,
        connection: Optional[Connection] = None
    ) -> Optional[Record]:
        
        """ 
            This method executes a list of SQL commands in a transaction to perform a soft delete operation.
            - `executables`: A list of `BaseExecutableSQL` objects representing the SQL commands to be executed.
            - `return_last`: A boolean flag indicating whether to return the result of the last executed
            - `connection`: An optional `Connection` object to use for executing the commands. If not provided, a new connection will be acquired from the pool.
            The method ensures that all commands are executed within a single transaction. If any command fails, the entire transaction will be rolled back to maintain data integrity.
        """
        
        if not executables:
            return None
        
        async with self._get_connection(connection) as connection:
            async with connection.transaction():
                for idx, executable in enumerate(executables, start=1):
                    
                    print("==="*10)
                    print(executable.preview())
                    print("==="*10)
                    
                    if idx != len(executables):
                        await connection.execute(executable.sql, *executable.values)
                    else:
                        result = await connection.fetchrow(executable.sql, *executable.values)
                    
                return result if return_last else None
              
    
         

