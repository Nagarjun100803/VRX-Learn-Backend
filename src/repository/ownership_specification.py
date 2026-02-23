from abc import ABC, abstractmethod
from src.commands.base import ID, UserID
from src.database import AsyncPgDBManager
from src.query_builder.base import BaseExecutableSQL
from dataclasses import dataclass


@dataclass
class BaseOwnershipSpec(ABC):
        
    entity_id: ID
    user_id: UserID
    db: AsyncPgDBManager

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
        


# NOTE: Create a CTE that handles enrollments.
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
    
    
class LessonOwnershipSpec(BaseOwnershipSpec):
    
    def get_executable(self):
        sql = """
            select
                1
            where exists(
                select
                    1
                from
                    lessons as l
                join
                    modules as m
                on
                    m.id = l.module_id
                join
                    courses as c
                on
                    c.id = m.course_id
                where(
                        (l.id = $(1) and 
                        (c.trainer_id = ($2) or c.manager_id = ($3)) and
                        (c.deleted_at is null and l.deleted_at is null and m.deleted_at is null)
                    )
            ;
        """
        return self.db.query_builder.build_executable(
            sql, values=(self.entity_id, self.user_id, self.user_id)
        )
        

class AssignmentOwnershipSpec(BaseOwnershipSpec):
    
    def get_executable(self):
        
        sql = """
            SELECT 
                1 
            WHERE EXISTS (
                SELECT 
                    1
                FROM 
                    assignments AS a
                JOIN 
                    courses AS c 
                ON 
                    c.id = a.course_id
                WHERE 
                    a.id = ($1)
                    AND (c.manager_id = ($2) OR c.trainer_id = ($3))
                    AND a.deleted_at IS NULL 
                    AND c.deleted_at IS NULL
                );
        """
        
        return self.db.query_builder.build_executable(
            sql=sql, values=(self.entity_id, self.user_id, self.user_id)
        )