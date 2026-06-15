from fastapi import APIRouter, status

from src.api.dependencies import CourseServiceDependency, CurrentAdmin
from src.api.docs.courses import (
    CREATE_COURSE,
    DELETE_COURSE,
    GET_COURSE,
    UPDATE_BASIC_INFO,
    UPDATE_PRE_RECORDED_COURSE_INFO,
)
from src.api.schemas.courses import (
    CourseCreateSchema,
    CourseInfoUpdateSchema,
    CourseOutSchema,
    RecordedCourseDetailsUpdateSchema,
)
from src.command.commands.base import CourseID
from src.command.commands.courses import (
    CourseCreate,
    CourseDelete,
    CourseGetByIDQuery,
    CourseInfoUpdate,
    RecordedCourseDetailsUpdate,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/{course_id}", response_model=CourseOutSchema, **GET_COURSE)
async def get_course(
    course_id: CourseID,
    course_service: CourseServiceDependency,
    current_user: CurrentAdmin,
):

    return await course_service.get(
        CourseGetByIDQuery(id=course_id, viewer_id=current_user)
    )


@router.post(
    "/",
    response_model=CourseOutSchema,
    status_code=status.HTTP_201_CREATED,
    **CREATE_COURSE,
)
async def create_course(
    course: CourseCreateSchema,
    course_service: CourseServiceDependency,
    current_user: CurrentAdmin,
):
    return await course_service.create(
        CourseCreate(**course.model_dump(), created_by=current_user)
    )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_COURSE)
async def delete_course(
    course_id: CourseID,
    course_service: CourseServiceDependency,
    current_user: CurrentAdmin,
):
    return await course_service.delete(
        CourseDelete(id=course_id, deleted_by=current_user)
    )


@router.patch(
    "/update-basic-info/{course_id}",
    response_model=CourseOutSchema,
    **UPDATE_BASIC_INFO,
)
async def update_basic_info(
    course_id: CourseID,
    course: CourseInfoUpdateSchema,
    course_service: CourseServiceDependency,
    current_user: CurrentAdmin,
):

    return await course_service.update(
        CourseInfoUpdate(**course.model_dump(), updated_by=current_user, id=course_id)
    )


@router.patch(
    "/update-prec-info/{course_id}",
    response_model=CourseOutSchema,
    **UPDATE_PRE_RECORDED_COURSE_INFO,
)
async def update_pre_recorded_course_info(
    course_id: CourseID,
    course: RecordedCourseDetailsUpdateSchema,
    course_service: CourseServiceDependency,
    current_user: CurrentAdmin,
):

    updated_course = await course_service.update(
        RecordedCourseDetailsUpdate(
            **course.model_dump(), updated_by=current_user, id=course_id
        )
    )

    return updated_course.details
