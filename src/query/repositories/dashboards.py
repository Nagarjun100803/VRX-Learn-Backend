from typing import Optional

from src.query.dto.dashboards import CourseCard, TrainerKPI, AssignedCourse
from src.query.repositories.base import BaseQueryRepository, map_to_dto



class TraineeDashboardQueryRepository(BaseQueryRepository):
    
    @map_to_dto(dto=CourseCard, dto_mode="list")
    async def enrolled_courses(self, trainee_id: int) -> list[CourseCard]:
        """Returns all the enrolled courses."""
        sql = """
            SELECT
                c.id AS course_id,
                c.title AS course_name,
                u.username AS trainer_name,
                c.thumbnail AS thumbnail_url
            FROM
                courses AS c
            JOIN
                enrollments AS e
            ON
                c.id = e.course_id
            LEFT JOIN
                users AS u
            ON
                u.id = c.trainer_id
            WHERE
                e.user_id = $1 AND
                e.deleted_at IS NULL AND
                c.deleted_at IS NULL
            ;
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainee_id, )
        )

        return await self.db.execute(executable, fetch_returns="all")

    
    @map_to_dto(dto=CourseCard, dto_mode="list")
    async def top_new_courses(self, n: int) -> list[CourseCard]:
        """Returns top n new courses."""
        sql = """
            SELECT
                c.id AS course_id,
                c.title AS course_name,
                u.username AS trainer_name,
                c.thumbnail AS thumbnail_url
            FROM
                courses AS c
            LEFT JOIN
                users AS u
            ON
                u.id = c.trainer_id
            WHERE
                c.deleted_at IS NULL
            ORDER BY
                c.created_at DESC
            LIMIT
                $1
            ;
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(n, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
        
    @map_to_dto(dto=CourseCard, dto_mode="single")
    async def current_course(self, trainee_id: int) -> Optional[CourseCard]:
        """Return a current course enrolled."""
        sql = """
            SELECT
                c.id AS course_id,
                c.title AS course_name,
                u.username AS trainer_name,
                c.thumbnail AS thumbnail_url
            FROM
                courses AS c
            JOIN
                enrollments AS e
            ON
                c.id = e.course_id
            LEFT JOIN
                users AS u
            ON
                c.trainer_id = u.id
            WHERE
                e.user_id = $1 AND
                e.deleted_at IS NULL AND
                c.deleted_at IS NULL
            ORDER BY
                e.created_at DESC
            LIMIT 1
            ;
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainee_id, )
        )
        return await self.db.execute(executable, fetch_returns="one")
        
        


class TrainerDashboardQueryReository(BaseQueryRepository):
    
    @map_to_dto(dto=TrainerKPI, dto_mode="single")
    async def kpis(self, trainer_id: int) -> Optional[TrainerKPI]:
        """Returns KPI's of a trainer"""
        sql = """
            SELECT
                COUNT(DISTINCT c.id) AS assigned_courses,
                COUNT(DISTINCT e.user_id) AS total_learners
            FROM
                courses AS c
            JOIN
                enrollments AS e
            ON
                e.course_id = c.id
            WHERE
                e.deleted_at IS NULL AND
                c.deleted_at IS NULL AND
                c.trainer_id = $1
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainer_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="one")


    @map_to_dto(dto=AssignedCourse, dto_mode="list")
    async def assigned_courses(self, trainer_id: int) -> list[AssignedCourse]:
        """List of courses assigned to a trainer."""    
        sql = """
            SELECT
                c.id AS course_id,
                c.title AS course_name,
                COUNT(e.user_id) AS total_trainees,
                c.thumbnail as thumbnail_url
            FROM
                courses AS c
            LEFT JOIN
                enrollments AS e
            ON
                c.id = e.course_id
            WHERE
                c.trainer_id = $1 AND
                c.deleted_at is NULL
            GROUP BY
                c.id, c.title, c.thumbnail
            ORDER BY
                c.created_at DESC
            ;
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainer_id, )
        )    
        
        return await self.db.execute(executable, fetch_returns="all")

