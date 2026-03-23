from typing import Optional

from pypika import Criterion, Order, PostgreSQLQuery, Parameter, functions

from src.pypika_query_builder import course_table, enrollment_table, user_table
from src.query.dto.dashboards import CourseCard, TrainerKPI, AssignedCourse
from src.query.repositories.base import BaseQueryRepository, map_to_dto


class TraineeDashboardQueryRepository(BaseQueryRepository):
    
    @map_to_dto(dto=CourseCard, dto_mode="list")
    async def enrolled_courses(self, trainee_id: int) -> list[CourseCard]:
        """Returns all the enrolled courses."""

        sql = PostgreSQLQuery\
            .from_(course_table)\
            .join(enrollment_table)\
            .on(course_table.id == enrollment_table.course_id)\
            .left_join(user_table)\
            .on(user_table.id == course_table.trainer_id)\
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.user_id == Parameter("$1"),
                        enrollment_table.deleted_at.isnull(),
                        course_table.deleted_at.isnull()
                    ]
                )
            ).select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                course_table.thumbnail.as_("thumbnail_url")
            ).get_sql()
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainee_id, )
        )

        return await self.db.execute(executable, fetch_returns="all")

    
    @map_to_dto(dto=CourseCard, dto_mode="list")
    async def top_new_courses(self, n: int) -> list[CourseCard]:
        """Returns top n new courses."""
        
        sql = PostgreSQLQuery\
            .from_(course_table)\
            .left_join(user_table)\
            .on(course_table.trainer_id == user_table.id)\
            .where(course_table.deleted_at.isnull())\
            .orderby(course_table.created_at)\
            .limit(limit=Parameter("$1"))\
            .select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                course_table.thumbnail.as_("thumbnail_url")
            ).get_sql()
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(n, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
        
    @map_to_dto(dto=CourseCard, dto_mode="single")
    async def current_course(self, trainee_id: int) -> Optional[CourseCard]:
        """Return a current course enrolled."""
        sql = PostgreSQLQuery\
            .from_(course_table)\
            .inner_join(enrollment_table)\
            .on(course_table.id == enrollment_table.course_id)\
            .left_join(user_table)\
            .on(course_table.trainer_id == user_table.id)\
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.user_id == Parameter("$1"),
                        enrollment_table.deleted_at.isnull(),
                        course_table.deleted_at.isnull()
                    ]
                )
            ).orderby(enrollment_table.created_at)\
            .limit(1)\
            .select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                course_table.thumbnail.as_("thumbnail_url")
            )\
            .get_sql()

        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainee_id, )
        )
        return await self.db.execute(executable, fetch_returns="one")
        
        


class TrainerDashboardQueryRepository(BaseQueryRepository):
    
    @map_to_dto(dto=TrainerKPI, dto_mode="single")
    async def kpis(self, trainer_id: int) -> Optional[TrainerKPI]:
        """Returns KPI's of a trainer"""
        sql = PostgreSQLQuery\
            .from_(course_table)\
            .join(enrollment_table)\
            .on(enrollment_table.course_id == course_table.id)\
            .where(
                Criterion.all(
                    terms=[
                        course_table.trainer_id == Parameter("$1"),
                        course_table.deleted_at.isnull(),
                        enrollment_table.deleted_at.isnull()
                    ]
                )
            ).select(
                functions.Count(course_table.id).distinct().as_("assigned_courses"),
                functions.Count(enrollment_table.user_id).distinct().as_("total_learners")
            ).get_sql()
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainer_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="one")


    @map_to_dto(dto=AssignedCourse, dto_mode="list")
    async def assigned_courses(self, trainer_id: int) -> list[AssignedCourse]:
        """List of courses assigned to a trainer."""   
        
        sql = PostgreSQLQuery\
            .from_(course_table)\
            .left_join(enrollment_table)\
            .on(course_table.id == enrollment_table.course_id)\
            .where(
                Criterion.all(
                    terms=[
                        course_table.trainer_id == Parameter("$1"),
                        course_table.deleted_at.isnull()
                    ]
                )
            ).groupby(
                course_table.id,
                course_table.title,
                course_table.thumbnail
            ).orderby(
                course_table.created_at, order=Order.desc
            ).select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                course_table.thumbnail.as_("thumbnail_url"),
                functions.Count(enrollment_table.user_id).as_("total_trainees")
            ).get_sql()
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(trainer_id, )
        )    
        
        return await self.db.execute(executable, fetch_returns="all")

