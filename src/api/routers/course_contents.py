from fastapi import APIRouter

from src.api.dependencies import (
    CurrentTraineeOrTrainer, CurrentTrainer, 
    TraineeCourseContentQueryServiceDependency, 
    TrainerCourseContentQueryServiceDependency
)
from src.command.commands.base import CourseID
from src.query.dto.course_contents import (
    CourseContentRequestSchema, TraineeCourseContent, 
    TrainerCourseContent
)

trainee_router = APIRouter(
    prefix="/course-contents/trainee",
    tags=["Course Contents", "Trainee Course Contents"]
)


@trainee_router.get("/{course_id}", response_model=TraineeCourseContent)
async def get_course_contents(
    course_id: CourseID,
    query_service: TraineeCourseContentQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer
):
    return await query_service.get_course_contents(
        CourseContentRequestSchema(
            course_id=course_id,
            viewer_id=current_user
        )
    )
    

trainer_router = APIRouter(
    prefix="/course-contents/trainer",
    tags=["Course Contents", "Trainer Course Contents"]
)


@trainer_router.get("/{course_id}", response_model=TrainerCourseContent)
async def get_course_contents(
    course_id: CourseID,
    query_service: TrainerCourseContentQueryServiceDependency,
    current_user: CurrentTrainer
):
    return await query_service.get_course_contents(
        CourseContentRequestSchema(
            course_id=course_id,
            viewer_id=current_user
        )
    )
