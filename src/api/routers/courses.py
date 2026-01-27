from fastapi import APIRouter, status
from src.api.dependencies import CurrentUser, CourseServiceDependency
from src.commands.base import CourseID
from src.commands.courses import CourseDelete, CourseGetByIDQuery, CourseCreate, CourseInfoUpdate, RecordedCourseDetailsUpdate
from src.api.schemas.courses import CourseOutSchema, CourseCreateSchema, CourseInfoUpdateSchema, RecordedCourseDetailsUpdateSchema



router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/{course_id}", response_model=CourseOutSchema)
async def get_course(
    course_id: CourseID,
    course_service: CourseServiceDependency,
    current_user: CurrentUser
):
    
    return await course_service.get(
        CourseGetByIDQuery(
            id=course_id,
            viewer_id=current_user
        )
    )
    

@router.post("/", response_model=CourseOutSchema, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreateSchema,
    course_service: CourseServiceDependency,
    current_user: CurrentUser
):
    return await course_service.create(
        CourseCreate(
            **course.model_dump(),
            created_by=current_user
        )
    )



@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: CourseID,
    course_service: CourseServiceDependency,
    current_user: CurrentUser
):
    return await course_service.delete(
        CourseDelete(
            id=course_id,
            deleted_by=current_user
        )
    )
    

@router.patch("/update-basic-info/{course_id}", response_model=CourseInfoUpdateSchema)
async def update_basic_info(
    course_id: CourseID,
    course: CourseInfoUpdateSchema,
    course_service: CourseServiceDependency,
    current_user: CurrentUser
):
    
    return await course_service.update(
        CourseInfoUpdate(
            **course.model_dump(),
            updated_by=current_user,
            id=course_id
        )
    )


@router.patch("/update-prec-info/{course_id}", response_model=RecordedCourseDetailsUpdateSchema)
async def update_pre_recorded_course_info(
    course_id: CourseID,
    course: RecordedCourseDetailsUpdateSchema,
    course_service: CourseServiceDependency,
    current_user: CurrentUser
):
    
    updated_course = await course_service.update(
        RecordedCourseDetailsUpdate(
            **course.model_dump(),
            updated_by=current_user,
            id=course_id   
        )
    )
    
    return updated_course.details
    
    