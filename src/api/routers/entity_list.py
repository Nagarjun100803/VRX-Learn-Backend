from fastapi import APIRouter

from src.api.dependencies import CurrentTraineeOrTrainer, CurrentTrainer, TraineeEntityListQueryServiceDependency, TrainerEntityListQueryServiceDependency
from src.command.commands.base import CourseID, ModuleID
from src.query.dto.entity_list import AssignmentDetail, AssignmentDetailWithDue, LessonDetail, ModuleDetail
from src.query.dto.request_schemas import CourseViewRequestSchema, ModuleViewRequestSchema


trainee_router = APIRouter(
    prefix="/list/trainee",
    tags=["List View", "Trainee List View"]
)


@trainee_router.get("/assignments/{course_id}", response_model=list[AssignmentDetail])
async def list_assignments(
    course_id: CourseID,
    query_service: TraineeEntityListQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer
):
    return await query_service.list_assignments(
        CourseViewRequestSchema(
            course_id=course_id,
            viewer_id=current_user
        )
    )
    
    

trainer_router = APIRouter(
    prefix="/list/trainer",
    tags=["List View", "Trainer List View"]
)


@trainer_router.get("/assignments/{course_id}", response_model=list[AssignmentDetailWithDue])
async def list_assignments(
    course_id: CourseID,
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentTrainer
):
    return await query_service.list_assignments(
        CourseViewRequestSchema(
            course_id=course_id,
            viewer_id=current_user
        )
    )
    
    
@trainer_router.get("/modules/{course_id}", response_model=list[ModuleDetail])
async def list_modules(
    course_id: CourseID,
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentTrainer
):
    return await query_service.list_modules(
        CourseViewRequestSchema(
            course_id=course_id,
            viewer_id=current_user
        )
    )
    
    

@trainer_router.get("/lessons/{module_id}", response_model=list[LessonDetail])
async def list_lessons(
    module_id: ModuleID,
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentTrainer
):
    return await query_service.list_lessons(
        ModuleViewRequestSchema(
            module_id=module_id,
            viewer_id=current_user
        )
    )
