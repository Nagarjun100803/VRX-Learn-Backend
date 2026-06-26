from typing import cast

from src.exceptions import CourseNotFoundError
from src.query.dto.course_overview import (
    CoursePreview,
    TraineeCourseOverview,
    TrainerCourseOverview,
)
from src.query.dto.request_schemas import CourseViewRequestSchema
from src.query.repositories.course_overview import (
    TraineeCourseOverviewQueryRepository,
    TraineeCoursePreviewQueryRepository,
    TrainerCourseOverviewQueryRepository,
)


class TraineeCoursePreviewQueryService:
    def __init__(
        self, trainee_course_preview_query_repo: TraineeCoursePreviewQueryRepository
    ) -> None:
        self.trainee_course_preview_query_repo = trainee_course_preview_query_repo

    async def get_preview(self, course_id: int) -> CoursePreview:
        preview = await self.trainee_course_preview_query_repo.preview(
            course_id=course_id
        )
        if preview is None:
            raise CourseNotFoundError(value=course_id)
        return preview


class TraineeCourseOverviewQueryService:
    def __init__(
        self, trainee_course_overview_query_repo: TraineeCourseOverviewQueryRepository
    ) -> None:
        self.trainee_course_overview_query_repo = trainee_course_overview_query_repo

    async def get_course_overview(
        self, query: CourseViewRequestSchema
    ) -> TraineeCourseOverview:
        # NOTE: At this time, the course existence is guaranteed by the authorization decorator.
        return cast(
            TraineeCourseOverview,
            await self.trainee_course_overview_query_repo.course_overview(
                course_id=query.course_id
            ),
        )


class TrainerCourseOverviewQueryService:
    def __init__(
        self, trainer_course_overview_query_repo: TrainerCourseOverviewQueryRepository
    ) -> None:
        self.trainer_course_overview_query_repo = trainer_course_overview_query_repo

    async def get_course_overview(
        self, query: CourseViewRequestSchema
    ) -> TrainerCourseOverview:
        # NOTE: At this time, the course existence is guaranteed by the authorization decorator.
        return cast(
            TrainerCourseOverview,
            await self.trainer_course_overview_query_repo.course_overview(
                course_id=query.course_id
            ),
        )
