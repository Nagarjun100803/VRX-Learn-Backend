from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.authorize import Authorize, AuthorizeOn
from src.api.dependencies import (
    TraineeCourseOverviewQueryServiceDependency,
    TraineeCoursePreviewQueryServiceDependency,
    TrainerCourseOverviewQueryServiceDependency,
)
from src.command.commands.base import CourseID, UserID
from src.query.dto.course_overview import (
    CoursePreview,
    TraineeCourseOverview,
    TrainerCourseOverview,
)
from src.query.dto.request_schemas import CourseViewRequestSchema

trainee_course_preview_router = APIRouter(
    prefix="/trainee/course-preview", tags=["Course Preview", "Trainee Course Preview"]
)


@trainee_course_preview_router.get("/{course_id}", response_model=CoursePreview)
async def get_course_preview_for_trainee(
    course_id: CourseID,
    query_service: TraineeCoursePreviewQueryServiceDependency,
    current_user: Annotated[
        UserID,
        Depends(Authorize(on=AuthorizeOn.COURSE_VIEW, entity_id_field="course_id")),
    ],
):
    return await query_service.get_preview(course_id=course_id)


trainee_router = APIRouter(
    prefix="/trainee/course-overview",
    tags=["Course Overview", "Trainee Course Overview"],
)


@trainee_router.get("/{course_id}", response_model=TraineeCourseOverview)
async def get_course_overview_for_trainee(
    course_id: CourseID,
    query_service: TraineeCourseOverviewQueryServiceDependency,
    current_user: Annotated[
        UserID,
        Depends(Authorize(on=AuthorizeOn.COURSE_VIEW, entity_id_field="course_id")),
    ],
):
    return await query_service.get_course_overview(
        query=CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


trainer_router = APIRouter(
    prefix="/trainer/course-overview",
    tags=["Course Overview", "Trainer Course Overview"],
)


@trainer_router.get("/{course_id}", response_model=TrainerCourseOverview)
async def get_course_overview_for_trainer(
    course_id: CourseID,
    query_service: TrainerCourseOverviewQueryServiceDependency,
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
    return await query_service.get_course_overview(
        query=CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )
