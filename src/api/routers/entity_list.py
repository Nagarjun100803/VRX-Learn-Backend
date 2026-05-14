from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import StringConstraints

from src.api.dependencies import (
    AdminEntityListQueryServiceDependency,
    CurrentAdmin,
    CurrentAdminOrTrainer,
    CurrentTraineeOrTrainer,
    TraineeEntityListQueryServiceDependency,
    TrainerEntityListQueryServiceDependency,
)
from src.command.commands.base import CourseID, ModuleID
from src.command.commands.users import UserRole
from src.query.dto.base import PageMeta, Paginated
from src.query.dto.entity_list import (
    AssignmentDetail,
    AssignmentDetailWithDue,
    CourseDetail,
    CourseFilters,
    CourseQueryParams,
    CourseSearchDetail,
    EnrollmentDetail,
    EnrollmentFilters,
    EnrollmentQueryParams,
    IssueDetail,
    IssueFilters,
    IssueQueryParams,
    LessonDetail,
    ModuleDetail,
    TraineeDetail,
    TraineeFilters,
    TraineeQueryParams,
    UserDetail,
    UserFilters,
    UserQueryParams,
    UserSearchDetail,
)
from src.query.dto.request_schemas import (
    CourseViewRequestSchema,
    ModuleViewRequestSchema,
)

admin_router = APIRouter(prefix="/list/admin", tags=["List View", "Admin List View"])


def _generate_filename(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"


@admin_router.get("/users/export", response_class=StreamingResponse)
async def export_users(
    filters: Annotated[UserFilters, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):

    filename = _generate_filename("users")
    generator = query_service.export_users(filters)

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@admin_router.get("/users", response_model=Paginated[UserDetail])
async def list_users(
    filters: Annotated[UserQueryParams, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):
    return await query_service.list_users(
        filters=UserFilters(
            name_or_email=filters.name_or_email,
            role=filters.role,
            sort_by_username=filters.sort_by_username,
            sort_by_created_at=filters.sort_by_created_at,
        ),
        page_meta=PageMeta(page=filters.page, limit=filters.limit),
    )


@admin_router.get("/courses/export", response_class=StreamingResponse)
async def export_courses(
    filters: Annotated[CourseFilters, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):

    filename = _generate_filename("courses")
    generator = query_service.export_courses(filters)

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@admin_router.get("/courses", response_model=Paginated[CourseDetail])
async def list_courses(
    filters: Annotated[CourseQueryParams, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):
    return await query_service.list_courses(
        filters=CourseFilters(
            course_name_or_trainer_name=filters.course_name_or_trainer_name,
            sort_by_course_name=filters.sort_by_course_name,
            sort_by_no_of_trainees=filters.sort_by_no_of_trainees,
            sort_by_created_at=filters.sort_by_created_at,
        ),
        page_meta=PageMeta(page=filters.page, limit=filters.limit),
    )


@admin_router.get("/enrollments/export", response_class=StreamingResponse)
async def export_enrollments(
    filters: Annotated[EnrollmentFilters, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):
    filename = _generate_filename("enrollments")
    generator = query_service.export_enrollments(filters)

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@admin_router.get("/enrollments", response_model=Paginated[EnrollmentDetail])
async def list_enrollments(
    filters: Annotated[EnrollmentQueryParams, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):
    return await query_service.list_enrollments(
        filters=EnrollmentFilters(
            name_or_email=filters.name_or_email,
            status=filters.status,
            role=filters.role,
            sort_by_course_name=filters.sort_by_course_name,
            sort_by_enrollment_date=filters.sort_by_enrollment_date,
        ),
        page_meta=PageMeta(page=filters.page, limit=filters.limit),
    )


@admin_router.get("/trainees/{course_id}/export", response_class=StreamingResponse)
async def export_trainees(
    course_id: CourseID,
    filters: Annotated[TraineeFilters, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):
    filename = _generate_filename("trainees")
    generator = query_service.export_trainees(course_id, filters)

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@admin_router.get("/trainees/{course_id}", response_model=Paginated[TraineeDetail])
async def list_trainees_for_admin(
    course_id: CourseID,
    filters: Annotated[TraineeQueryParams, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):

    return await query_service.list_trainees(
        course_id=course_id,
        filters=TraineeFilters(
            name=filters.name,
            role=filters.role,
            sort_by_enrollment_date=filters.sort_by_enrollment_date,
            sort_by_username=filters.sort_by_username,
        ),
        page_meta=PageMeta(page=filters.page, limit=filters.limit),
    )


@admin_router.get("/issues", response_model=Paginated[IssueDetail])
async def list_issues(
    filters: Annotated[IssueQueryParams, Depends()],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):
    return await query_service.list_issues(
        filters=IssueFilters(
            category=filters.category, status=filters.status, role=filters.role
        ),
        page_mata=PageMeta(page=filters.page, limit=filters.limit),
    )


admin_search_router = APIRouter(
    prefix="/admin/search", tags=["Admin Search", "Admin List View"]
)


@admin_search_router.get("/users", response_model=list[UserSearchDetail])
async def search_users(
    username_or_email: Annotated[str, StringConstraints(to_lower=True)],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
    role: Annotated[Optional[list[UserRole]], Query()] = None,
):
    role_to_filter = tuple() if role is None else tuple(role)
    return await query_service.search_users(
        username_or_email=username_or_email, role=role_to_filter
    )


@admin_search_router.get("/courses", response_model=list[CourseSearchDetail])
async def search_courses(
    course_name: Annotated[str, StringConstraints(to_upper=True)],
    query_service: AdminEntityListQueryServiceDependency,
    current_user: CurrentAdmin,
):

    return await query_service.search_course(course_name=course_name)


trainee_router = APIRouter(
    prefix="/list/trainee", tags=["List View", "Trainee List View"]
)


@trainee_router.get(
    "/assignments/{course_id}", response_model=list[AssignmentDetail], deprecated=True
)
async def list_assignments_for_trainee(
    course_id: CourseID,
    query_service: TraineeEntityListQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer,
):
    return await query_service.list_assignments(
        CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


trainer_router = APIRouter(
    prefix="/list/trainer", tags=["List View", "Trainer List View"]
)


@trainer_router.get(
    "/assignments/{course_id}",
    response_model=list[AssignmentDetailWithDue],
    deprecated=True,
)
async def list_assignments_for_trainer(
    course_id: CourseID,
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):
    return await query_service.list_assignments(
        CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


@trainer_router.get("/modules/{course_id}", response_model=list[ModuleDetail])
async def list_modules(
    course_id: CourseID,
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):
    return await query_service.list_modules(
        CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


@trainer_router.get("/lessons/{module_id}", response_model=list[LessonDetail])
async def list_lessons(
    module_id: ModuleID,
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):
    return await query_service.list_lessons(
        ModuleViewRequestSchema(module_id=module_id, viewer_id=current_user)
    )


@trainer_router.get("/trainees/{course_id}", response_model=Paginated[TraineeDetail])
async def list_trainees_for_trainer(
    course_id: CourseID,
    filters: Annotated[TraineeQueryParams, Depends()],
    query_service: TrainerEntityListQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):

    return await query_service.list_trainees(
        query=CourseViewRequestSchema(course_id=course_id, viewer_id=current_user),
        filters=TraineeFilters(
            name=filters.name,
            role=filters.role,
            sort_by_enrollment_date=filters.sort_by_enrollment_date,
            sort_by_username=filters.sort_by_username,
        ),
        page_meta=PageMeta(page=filters.page, limit=filters.limit),
    )
