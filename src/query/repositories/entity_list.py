from pypika import Criterion, Parameter, PostgreSQLQuery

from src.pypika_query_builder import assignment_table, module_table, lesson_table
from src.query.dto.entity_list import AssignmentDetailWithDue, LessonDetail, ModuleDetail
from src.query.repositories.base import BaseQueryRepository, map_to_dto



class EntityListQueryRepository(BaseQueryRepository):
    
    @map_to_dto(dto=ModuleDetail, dto_mode="list")
    async def modules(self, course_id: int) -> list[ModuleDetail]:
        
        sql = PostgreSQLQuery\
            .from_(module_table)\
            .where(
                Criterion.all(
                    terms=[
                        module_table.course_id == Parameter("$1"),
                        module_table.deleted_at.isnull()
                    ]
                )
            ).orderby(
                module_table.position_string
            ).select(
                module_table.id,
                module_table.title
            ).get_sql()
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
    
    
    @map_to_dto(dto=LessonDetail, dto_mode="list")
    async def lessons(self, module_id: int) -> list[LessonDetail]:
        
        sql = PostgreSQLQuery\
            .from_(lesson_table)\
            .where(
                Criterion.all(
                    terms=[
                        lesson_table.module_id == Parameter("$1"),
                        lesson_table.deleted_at.isnull()
                    ]
                )
            ).orderby(
                lesson_table.position_string
            ).select(
                lesson_table.id,
                lesson_table.title
            ).get_sql()    
    
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(module_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
    
    @map_to_dto(dto=AssignmentDetailWithDue, dto_mode="list")
    async def assignments(self, course_id: int) -> list[AssignmentDetailWithDue]:
        
        sql = PostgreSQLQuery\
            .from_(assignment_table)\
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == Parameter("$1"),
                        assignment_table.deleted_at.isnull()    
                    ]
                )
            ).orderby(
                assignment_table.due_date
            ).select(
                assignment_table.id,
                assignment_table.title,
                assignment_table.due_date
            ).get_sql()
            
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")

