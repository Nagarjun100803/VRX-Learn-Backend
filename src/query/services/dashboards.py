from typing import Optional

from src.cache import CacheKey, CacheService, CacheTag
from src.query.dto.dashboards import (
    AdminCourseCard,
    AdminKPI,
    AssignedCourse,
    CourseCard,
    TrainerKPI,
)
from src.query.repositories import (
    TraineeDashboardQueryRepository,
    TrainerDashboardQueryRepository,
)
from src.query.repositories.dashboards import AdminDashboardQueryRepository


class TraineeDashboardQueryService:
    def __init__(
        self,
        trainee_dashboard_query_repo: TraineeDashboardQueryRepository,
        cache_service: CacheService,
    ) -> None:
        self.trainee_dashboard_query_repo = trainee_dashboard_query_repo
        self.cache_service = cache_service

    async def list_enrolled_courses(self, trainee_id: int) -> list[CourseCard]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINEE_DASHBOARD_ENROLLED_COURSES.format(
                trainee_id=trainee_id
            ),
            model=list[CourseCard],
            ttl=300,
            negative_ttl=30,
            fetch_func=lambda: self.trainee_dashboard_query_repo.enrolled_courses(
                trainee_id=trainee_id
            ),
            tags={CacheTag.TRAINEE_ENROLLED_COURSES.format(trainee_id=trainee_id)},
        )

    async def list_top_new_courses(self, n: int) -> list[CourseCard]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINEE_DASHBOARD_TOP_NEW_COURSES.format(n=n),
            model=list[CourseCard],
            ttl=300,
            negative_ttl=30,
            fetch_func=lambda: self.trainee_dashboard_query_repo.top_new_courses(n=n),
            tags={CacheTag.TRAINEE_TOP_NEW_COURSES},
        )

    async def get_current_course(self, trainee_id: int) -> Optional[CourseCard]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINEE_DASHBOARD_CURRENT_COURSE.format(trainee_id=trainee_id),
            model=Optional[CourseCard],
            ttl=300,
            negative_ttl=30,
            fetch_func=lambda: self.trainee_dashboard_query_repo.current_course(
                trainee_id=trainee_id
            ),
            tags={CacheTag.TRAINEE_CURRENT_COURSE.format(trainee_id=trainee_id)},
        )


class TrainerDashboardQueryService:
    def __init__(
        self,
        trainer_dashboard_query_repo: TrainerDashboardQueryRepository,
        cache_service: CacheService,
    ) -> None:
        self.trainer_dashboard_query_repo = trainer_dashboard_query_repo
        self.cache_service = cache_service

    async def get_kpis(self, trainer_id: int) -> Optional[TrainerKPI]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINER_DASHBOARD_KPIS.format(trainer_id=trainer_id),
            model=Optional[TrainerKPI],
            ttl=300,
            negative_ttl=30,
            fetch_func=lambda: self.trainer_dashboard_query_repo.kpis(
                trainer_id=trainer_id
            ),
            tags={CacheTag.TRAINER_KPIS.format(trainer_id=trainer_id)},
        )

    async def list_assigned_courses(self, trainer_id: int) -> list[AssignedCourse]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINER_DASHBOARD_ASSIGNED_COURSES.format(
                trainer_id=trainer_id
            ),
            model=list[AssignedCourse],
            ttl=300,
            negative_ttl=30,
            fetch_func=lambda: self.trainer_dashboard_query_repo.assigned_courses(
                trainer_id=trainer_id
            ),
            tags={CacheTag.TRAINER_ASSIGNED_COURSES.format(trainer_id=trainer_id)},
        )


class AdminDashboardQueryService:
    def __init__(
        self,
        admin_dashboard_query_repo: AdminDashboardQueryRepository,
        cache_service: CacheService,
    ) -> None:
        self.admin_dashboard_query_repo = admin_dashboard_query_repo
        self.cache_service = cache_service

    async def get_kpis(self) -> Optional[AdminKPI]:

        return await self.cache_service.get_or_set(
            key=CacheKey.ADMIN_DASHBOARD_KPIS,
            model=Optional[AdminKPI],
            ttl=300,
            fetch_func=self.admin_dashboard_query_repo.kpis,
            negative_ttl=30,
            tags={CacheTag.ADMIN_KPIS},
        )

    async def list_top_enrolled_courses(self, n: int) -> list[AdminCourseCard]:

        return await self.cache_service.get_or_set(
            key=CacheKey.ADMIN_DASHBOARD_TOP_ENROLLED_COURSES.format(n=n),
            model=list[AdminCourseCard],
            ttl=300,
            negative_ttl=30,
            fetch_func=lambda: self.admin_dashboard_query_repo.top_enrolled_courses(
                n=n
            ),
            tags={CacheTag.ADMIN_TOP_ENROLLED_COURSES},
        )
