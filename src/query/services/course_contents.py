from typing import Optional

from src.auth.auth import AuthService, require_authorization
from src.auth.permission_policy import Action, Entity
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
        self,
        trainee_course_content_repo: TraineeCourseContentQueryRepository,
        auth_service: AuthService,
    ) -> None:

        self.trainee_course_content_repo = trainee_course_content_repo
        self.auth_service = auth_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="course_id",
        object_name="query",
    )
    async def get_course_contents(
        self, query: CourseContentRequestSchema
    ) -> Optional[TraineeCourseContent]:
        return await self.trainee_course_content_repo.course_contents(
            course_id=query.course_id, user_id=query.viewer_id
        )


class TrainerCourseContentQueryService:
    def __init__(
        self,
        trainer_course_content_repo: TrainerCourseContentQueryRepository,
        auth_service: AuthService,
    ) -> None:

        self.trainer_course_content_repo = trainer_course_content_repo
        self.auth_service = auth_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="course_id",
        object_name="query",
    )
    async def get_course_contents(
        self, query: CourseContentRequestSchema
    ) -> Optional[TrainerCourseContent]:
        return await self.trainer_course_content_repo.course_contents(
            course_id=query.course_id
        )
