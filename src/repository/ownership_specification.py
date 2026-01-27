from typing import Optional, Union
from abc import ABC, abstractmethod
from src.commands.base import ID, UserID
from src.database import AsyncPgDBManager, async_db_manager
from src.query_builder.base import BaseExecutableSQL



class BaseOwnershipSpec(ABC):
    
    def __init__(
        self,
        entity_id: ID,
        user_id: UserID,
        db: Optional[AsyncPgDBManager] = None,
    ):
        
        self.db = db or async_db_manager
        self.user_id = user_id
        self.entity_id = entity_id
        
    
    
    @abstractmethod
    def get_executable(self) -> BaseExecutableSQL:
        """Returns the BaseExecutable sql to check ownership."""
        
    
    async def is_satisfied(self) -> bool:
        # Not created as abstract method, since it hanldes in all 
        # subclasses and not necessary to repeat the same in subclass.
        """Checks for the ownership of an entity."""
        executable = self.get_executable()
        res = await self.db.execute(executable, fetch_returns="one")
        return bool(res)
        


class UserOwnershipSpec(BaseOwnershipSpec):
    
    def get_executable(self):
        sql = """
            select  
                1
            from 
                users
            where 
                id = $1 and (
                    created_by = $2 or 
                    id = $3
                )
        """
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id)
        )



class CourseOwnershipSpec(BaseOwnershipSpec):
    
    def get_executable(self):
        sql = """
            select
                1
            from 
                courses
            where
                (id = ($1)) and (
                    trainer_id = ($2) or
                    manager_id = ($3)
                )
            ;
        """
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id)
        )
        

        
class ModuleOwnershipSpec(BaseOwnershipSpec):
    
    def get_executable(self):
        sql = """
            select 
                1
            from 
                modules as m
            join
                courses as c
            on 
                c.id = m.course_id
            where 
                m.id = ($1) and (
                    c.trainer_id = $2 or 
                    c.manager_id = $3
                )
            ; 
        """
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id)
        )
    
    
    

