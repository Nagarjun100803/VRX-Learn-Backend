from typing import cast

from src.auth import Action, AuthService, Entity, require_authorization
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
    ) -> None:
        self.trainee_course_overview_query_repo = trainee_course_overview_query_repo
        self.auth_service = auth_service

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
        # NOTE: At this time, the course existance is guaranteed by the authorization decorator.
        return cast(
            TraineeCourseOverview,
            await self.trainee_course_overview_query_repo.course_overview(
                course_id=query.course_id
            ),
        )


class TrainerCourseOverviewQueryService:
    def __init__(
        self,
        trainer_course_overview_query_repo: TrainerCourseOverviewQueryRepository,
        auth_service: AuthService,
    ) -> None:
        self.trainer_course_overview_query_repo = trainer_course_overview_query_repo
        self.auth_service = auth_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="course_id",
        object_name="query",
    )
    async def get_course_overview(
        self, query: CourseViewRequestSchema
    ) -> TrainerCourseOverview:
        # NOTE: At this time, the course existance is guaranteed by the authorization decorator.
        return cast(
            TrainerCourseOverview,
            await self.trainer_course_overview_query_repo.course_overview(
                course_id=query.course_id
            ),
        )
