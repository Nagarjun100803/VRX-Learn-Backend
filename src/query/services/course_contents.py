from typing import Optional

from src.query.dto.course_contents import (
    CourseContentRequestSchema,
    TraineeCourseContent,
    TrainerCourseContent,
)
from src.query.repositories.course_contents import (
    TraineeCourseContentQueryRepository,
    TrainerCourseContentQueryRepository,
)


class TraineeCourseContentQueryService:
    def __init__(
        self, trainee_course_content_repo: TraineeCourseContentQueryRepository
    ) -> None:

        self.trainee_course_content_repo = trainee_course_content_repo

    async def get_course_contents(
        self, query: CourseContentRequestSchema
    ) -> Optional[TraineeCourseContent]:
        return await self.trainee_course_content_repo.course_contents(
            course_id=query.course_id, user_id=query.viewer_id
        )


class TrainerCourseContentQueryService:
    def __init__(
        self, trainer_course_content_repo: TrainerCourseContentQueryRepository
    ) -> None:

        self.trainer_course_content_repo = trainer_course_content_repo

    async def get_course_contents(
        self, query: CourseContentRequestSchema
    ) -> Optional[TrainerCourseContent]:
        return await self.trainer_course_content_repo.course_contents(
            course_id=query.course_id
        )
