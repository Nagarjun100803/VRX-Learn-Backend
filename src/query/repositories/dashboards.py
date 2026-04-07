from typing import Optional, cast

from pypika import Criterion, Order, Parameter, PostgreSQLQuery, Table
from pypika import functions as fn
from pypika.terms import ValueWrapper

from src.database import ExecutableSQL
from src.pypika_query_builder import (
    CustomOrder,
    course_table,
    enrollment_table,
    user_table,
)
from src.query.dto.dashboards import (
    AdminCourseCard,
    AdminKPI,
    AssignedCourse,
    CourseCard,
    TrainerKPI,
)
from src.query.repositories.base import BaseQueryRepository, map_to_dto


class TraineeDashboardQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=CourseCard, dto_mode="list")
    async def enrolled_courses(self, trainee_id: int) -> list[CourseCard]:
        """Returns all the enrolled courses."""

        sql = (
            PostgreSQLQuery.from_(course_table)
            .join(enrollment_table)
            .on(course_table.id == enrollment_table.course_id)
            .left_join(user_table)
            .on(user_table.id == course_table.trainer_id)
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.user_id == Parameter("$1"),
                        enrollment_table.deleted_at.isnull(),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                course_table.thumbnail.as_("thumbnail_url"),
            )
            .get_sql()
        )
        executable = ExecutableSQL(sql, values=(trainee_id,))

        return cast(
            list[CourseCard], await self.db.execute(executable, fetch_returns="all")
        )

    @map_to_dto(dto=CourseCard, dto_mode="list")
    async def top_new_courses(self, n: int) -> list[CourseCard]:
        """Returns top n new courses."""

        sql = (
            PostgreSQLQuery.from_(course_table)
            .left_join(user_table)
            .on(course_table.trainer_id == user_table.id)
            .where(course_table.deleted_at.isnull())
            .orderby(course_table.created_at)
            .limit(limit=Parameter("$1"))  # type: ignore
            .select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                course_table.thumbnail.as_("thumbnail_url"),
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql, values=(n,))

        return cast(
            list[CourseCard], await self.db.execute(executable, fetch_returns="all")
        )

    @map_to_dto(dto=CourseCard, dto_mode="single")
    async def current_course(self, trainee_id: int) -> Optional[CourseCard]:
        """Return a current course enrolled."""
        sql = (
            PostgreSQLQuery.from_(course_table)
            .inner_join(enrollment_table)
            .on(course_table.id == enrollment_table.course_id)
            .left_join(user_table)
            .on(course_table.trainer_id == user_table.id)
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.user_id == Parameter("$1"),
                        enrollment_table.deleted_at.isnull(),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
            .orderby(enrollment_table.created_at)
            .limit(1)
            .select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                course_table.thumbnail.as_("thumbnail_url"),
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql, values=(trainee_id,))
        return cast(
            Optional[CourseCard], await self.db.execute(executable, fetch_returns="one")
        )


class TrainerDashboardQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=TrainerKPI, dto_mode="single")
    async def kpis(self, trainer_id: int) -> Optional[TrainerKPI]:
        """Returns KPI's of a trainer"""
        sql = (
            PostgreSQLQuery.from_(course_table)
            .join(enrollment_table)
            .on(enrollment_table.course_id == course_table.id)
            .where(
                Criterion.all(
                    terms=[
                        course_table.trainer_id == Parameter("$1"),
                        course_table.deleted_at.isnull(),
                        enrollment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                fn.Count(course_table.id).distinct().as_("assigned_courses"),
                fn.Count(enrollment_table.user_id).distinct().as_("total_learners"),
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql, values=(trainer_id,))

        return cast(
            Optional[TrainerKPI], await self.db.execute(executable, fetch_returns="one")
        )

    @map_to_dto(dto=AssignedCourse, dto_mode="list")
    async def assigned_courses(self, trainer_id: int) -> list[AssignedCourse]:
        """List of courses assigned to a trainer."""

        sql = (
            PostgreSQLQuery.from_(course_table)
            .left_join(enrollment_table)
            .on(course_table.id == enrollment_table.course_id)
            .where(
                Criterion.all(
                    terms=[
                        course_table.trainer_id == Parameter("$1"),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
            .groupby(course_table.id, course_table.title, course_table.thumbnail)
            .orderby(course_table.created_at, order=Order.desc)
            .select(
                course_table.id.as_("course_id"),
                course_table.title.as_("course_name"),
                course_table.thumbnail.as_("thumbnail_url"),
                fn.Count(enrollment_table.user_id).as_("total_trainees"),
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql, values=(trainer_id,))

        return cast(
            list[AssignedCourse], await self.db.execute(executable, fetch_returns="all")
        )


class AdminDashboardQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=AdminKPI, dto_mode="single")
    async def kpis(self) -> AdminKPI:

        total_users_query = (
            PostgreSQLQuery.from_(user_table)
            .where(user_table.deleted_at.isnull())
            .select(fn.Count(user_table.id).as_("total_users"))
        )

        total_courses_query = (
            PostgreSQLQuery.from_(course_table)
            .where(course_table.deleted_at.isnull())
            .select(fn.Count(course_table.id).as_("total_courses"))
        )

        total_enrollments_query = (
            PostgreSQLQuery.from_(enrollment_table)
            .where(enrollment_table.deleted_at.isnull())
            .select(fn.Count(enrollment_table.id).as_("total_enrollments"))
        )

        sql = PostgreSQLQuery.select(
            total_users_query, total_courses_query, total_enrollments_query
        ).get_sql()

        executable = ExecutableSQL(sql, values=tuple())

        return cast(AdminKPI, await self.db.execute(executable, fetch_returns="one"))

    @map_to_dto(dto=AdminCourseCard, dto_mode="list")
    async def top_enrolled_courses(self, n: int) -> list[AdminCourseCard]:

        enrollment_subquery = (
            PostgreSQLQuery.from_(enrollment_table)
            .where(enrollment_table.deleted_at.isnull())
            .groupby(enrollment_table.course_id)
            .select(
                enrollment_table.course_id,
                fn.Count(enrollment_table.user_id).as_("total_trainees"),
            )
        )

        enrollment_cte = Table("enrollment_cte")  # reference table.

        sql = (
            PostgreSQLQuery.with_(enrollment_subquery, enrollment_cte._table_name)
            .from_(course_table)
            .join(user_table)
            .on(course_table.trainer_id == user_table.id)
            .left_join(enrollment_cte)
            .on(course_table.id == enrollment_cte.course_id)
            .where(course_table.deleted_at.isnull())
            .orderby(enrollment_cte.total_trainees, order=CustomOrder.desc_nulls_last)
            .limit(n)
            .select(
                course_table.id,
                course_table.title.as_("course_name"),
                user_table.username.as_("trainer_name"),
                fn.Coalesce(enrollment_cte.total_trainees, ValueWrapper(0)).as_(
                    "total_trainees"
                ),
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql, values=tuple())

        result = await self.db.execute(executable, fetch_returns="all")
        return cast(list[AdminCourseCard], result)
