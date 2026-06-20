from typing import Annotated, Optional

from fastapi import APIRouter
from fastapi.params import Depends

from src.api.authorize import Authorize, AuthorizeOn
from src.api.dependencies import (
    TraineeCourseContentQueryServiceDependency,
    TrainerCourseContentQueryServiceDependency,
)
from src.command.commands.base import CourseID, UserID
from src.query.dto.course_contents import (
    CourseContentRequestSchema,
    TraineeCourseContent,
    TrainerCourseContent,
)

trainee_router = APIRouter(
    prefix="/course-contents/trainee",
    tags=["Course Contents", "Trainee Course Contents"],
)


@trainee_router.get("/{course_id}", response_model=Optional[TraineeCourseContent])
async def get_course_contents_for_trainee(
    course_id: CourseID,
    query_service: TraineeCourseContentQueryServiceDependency,
    current_user: Annotated[
        UserID,
        Depends(Authorize(on=AuthorizeOn.COURSE_VIEW, entity_id_field="course_id")),
    ],
):
    return await query_service.get_course_contents(
        CourseContentRequestSchema(course_id=course_id, viewer_id=current_user)
    )


trainer_router = APIRouter(
    prefix="/course-contents/trainer",
    tags=["Course Contents", "Trainer Course Contents"],
)


@trainer_router.get("/{course_id}", response_model=Optional[TrainerCourseContent])
async def get_course_contents_for_trainer(
    course_id: CourseID,
    query_service: TrainerCourseContentQueryServiceDependency,
    current_user: Annotated[
        UserID,
        Depends(
            Authorize(
                on=AuthorizeOn.COURSE_VIEW,
                entity_id_field="course_id",
                allowed_user_roles={"admin", "trainer"},
            )
        ),
    ],
):
    return await query_service.get_course_contents(
        CourseContentRequestSchema(course_id=course_id, viewer_id=current_user)
    )
