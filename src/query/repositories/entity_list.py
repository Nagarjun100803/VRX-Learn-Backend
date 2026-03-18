from src.query.dto.entity_list import AssignmentDetailWithDue, LessonDetail, ModuleDetail
from src.query.repositories.base import BaseQueryRepository, map_to_dto



class EntityListQueryRepository(BaseQueryRepository):
    
    @map_to_dto(dto=ModuleDetail, dto_mode="list")
    async def modules(self, course_id: int) -> list[ModuleDetail]:
        sql = """
            SELECT
                m.id,
                m.title
            FROM
                modules AS m
            WHERE
                m.course_id = $1 AND
                m.deleted_at IS NULL
            ORDER BY
                m.position_string
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
    
    
    @map_to_dto(dto=LessonDetail, dto_mode="list")
    async def lessons(self, module_id: int) -> list[LessonDetail]:
        sql = """
            SELECT
                l.id,
                l.title
            FROM
                lessons AS l
            WHERE
                l.module_id = $1 AND
                l.deleted_at IS NULL
            ORDER BY
                l.position_string
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(module_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
    
    @map_to_dto(dto=AssignmentDetailWithDue, dto_mode="list")
    async def assignments(self, course_id: int) -> list[AssignmentDetailWithDue]:
        sql = """
            SELECT
                a.id,
                a.title,
                a.due_date
            FROM
                assignments AS a
            WHERE
                a.course_id = $1 AND
                a.deleted_at IS NULL
            ORDER BY
                a.due_date
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")

