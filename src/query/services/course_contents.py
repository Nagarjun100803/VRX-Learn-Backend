from typing import Optional

from src.auth.auth import AuthService, require_authorization
from src.auth.permission_policy import Action, Entity
from src.cache import CacheKey, CacheService, CacheTag
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
        cache_service: CacheService,
    ) -> None:

        self.trainee_course_content_repo = trainee_course_content_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

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

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINEE_COURSE_CONTENTS.format(course_id=query.course_id),
            model=Optional[TraineeCourseContent],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainee_course_content_repo.course_contents(
                course_id=query.course_id
            ),
            tags={CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=query.course_id)},
        )


class TrainerCourseContentQueryService:
    def __init__(
        self,
        trainer_course_content_repo: TrainerCourseContentQueryRepository,
        auth_service: AuthService,
        cache_service: CacheService,
    ) -> None:

        self.trainer_course_content_repo = trainer_course_content_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

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

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINER_COURSE_CONTENTS.format(course_id=query.course_id),
            model=Optional[TrainerCourseContent],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainer_course_content_repo.course_contents(
                course_id=query.course_id
            ),
            tags={CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=query.course_id)},
        )
