from typing import Optional, cast

from src.auth import Action, AuthService, Entity, require_authorization
from src.cache import CacheKey, CacheService
from src.query.dto.course_overview import TraineeCourseOverview, TrainerCourseOverview
from src.query.dto.request_schemas import CourseViewRequestSchema
from src.query.repositories.course_overview import (
    TraineeCourseOverviewQueryRepository,
    TrainerCourseOverviewQueryRepository,
)


class TraineeCourseOverviewQueryService:
    def __init__(
        self,
        trainee_course_overview_query_repo: TraineeCourseOverviewQueryRepository,
        auth_service: AuthService,
        cache_service: CacheService,
    ) -> None:
        self.trainee_course_overview_query_repo = trainee_course_overview_query_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="course_id",
        object_name="query",
    )
    async def get_course_overview(
        self, query: CourseViewRequestSchema
    ) -> TraineeCourseOverview:

        return cast(
            TraineeCourseOverview,
            await self.cache_service.get_or_set(
                key=CacheKey.TRAINEE_COURSE_OVERVIEW.format(course_id=query.course_id),
                model=TraineeCourseOverview,
                ttl=600,
                negative_ttl=120,
                fetch_func=lambda: (
                    self.trainee_course_overview_query_repo.course_overview(
                        course_id=query.course_id
                    )
                ),
            ),
        )


class TrainerCourseOverviewQueryService:
    def __init__(
        self,
        trainer_course_overview_query_repo: TrainerCourseOverviewQueryRepository,
        auth_service: AuthService,
        cache_service: CacheService,
    ) -> None:
        self.trainer_course_overview_query_repo = trainer_course_overview_query_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="course_id",
        object_name="query",
    )
    async def get_course_overview(
        self, query: CourseViewRequestSchema
    ) -> Optional[TrainerCourseOverview]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINER_COURSE_OVERVIEW.format(course_id=query.course_id),
            model=Optional[TrainerCourseOverview],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainer_course_overview_query_repo.course_overview(
                course_id=query.course_id
            ),
        )
