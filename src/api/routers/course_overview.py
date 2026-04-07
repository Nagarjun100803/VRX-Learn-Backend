from typing import Optional

from fastapi import APIRouter

from src.api.dependencies import (
    CurrentAdminOrTrainer,
    CurrentTraineeOrTrainer,
    TraineeCourseOverviewQueryServiceDependency,
    TrainerCourseOverviewQueryServiceDependency,
)
from src.command.commands.base import CourseID
from src.query.dto.course_overview import TraineeCourseOverview, TrainerCourseOverview
from src.query.dto.request_schemas import CourseViewRequestSchema

trainee_router = APIRouter(
    prefix="/trainee/course-overview",
    tags=["Course Overview", "Trainee Course Overview"],
)


@trainee_router.get("/{course_id}", response_model=TraineeCourseOverview)
async def get_course_overview_for_trainee(
    course_id: CourseID,
    query_service: TraineeCourseOverviewQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer,
):
    return await query_service.get_course_overview(
        query=CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


trainer_router = APIRouter(
    prefix="/trainer/course-overview",
    tags=["Course Overview", "Trainer Course Overview"],
)


@trainer_router.get("/{course_id}", response_model=Optional[TrainerCourseOverview])
async def get_course_overview_for_trainer(
    course_id: CourseID,
    query_service: TrainerCourseOverviewQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):
    return await query_service.get_course_overview(
        query=CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )
