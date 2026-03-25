from typing import Annotated

from fastapi import APIRouter
from pydantic import Field

from src.api.dependencies import(
    AdminDashboardQueryServiceDependency,
    CurrentAdmin,
    CurrentTraineeOrTrainer,
    CurrentTrainer,
    TraineeDashboardQueryServiceDependency,
    TrainerDashboardQueryServiceDependency,
)
from src.query.dto.dashboards import AdminKPI, AssignedCourse, CourseCard, TrainerKPI


admin_router = APIRouter(
    prefix="/dashboard/admin",
    tags=["Dashboard", "Admin Dashboard"]
)

@admin_router.get("/kpis", response_model=AdminKPI)
async def get_kpis(
    query_service: AdminDashboardQueryServiceDependency,
    current_user: CurrentAdmin
):
    return await query_service.get_kpis()


@admin_router.get("/top-enrolled-courses")
async def list_top_enrolled_courses(
    n: Annotated[int, Field(gt=0)],
    query_service: AdminDashboardQueryServiceDependency,
    current_user: CurrentAdmin
):
    return await query_service.list_top_enrolled_courses(n=n)



trainee_router = APIRouter(
    prefix="/dashboard/trainee", 
    tags=["Dashboard",  "Trainee Dashboard"]
)


@trainee_router.get("/enrolled-courses", response_model=list[CourseCard])
async def list_enrolled_courses(
    query_service: TraineeDashboardQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer 
):
    return await query_service.list_enrolled_courses(trainee_id=current_user)



@trainee_router.get("/top-new-courses/{n}", response_model=list[CourseCard])
async def list_top_n_new_courses(
    n: int,
    query_service: TraineeDashboardQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer
):
    return await query_service.list_top_new_courses(n)



@trainee_router.get("/current-course", response_model=CourseCard)
async def get_current_course(
    query_service: TraineeDashboardQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer
):
    return await query_service.get_current_course(trainee_id=current_user)



trainer_router = APIRouter(
    prefix="/dashboard/trainer",
    tags=["Dashboard", "Trainer Dashboard"]
)

@trainer_router.get("/kpis", response_model=TrainerKPI)
async def get_kpis(
    query_service: TrainerDashboardQueryServiceDependency,
    current_user: CurrentTrainer
):
    return await query_service.get_kpis(trainer_id=current_user)



@trainer_router.get("/assigned-courses", response_model=list[AssignedCourse])
async def list_assigned_courses(
    query_service: TrainerDashboardQueryServiceDependency,
    current_user: CurrentTrainer
):
    return await query_service.list_assigned_courses(trainer_id=current_user)

