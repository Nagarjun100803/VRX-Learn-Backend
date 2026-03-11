from fastapi import APIRouter, status
from src.api.dependencies import EnrollmentServiceDependency, CurrentUser
from src.command.commands.base import EnrollmentID
from src.command.commands.enrollments import EnrollmentCreate, EnrollmentDelete, EnrollmentGet, EnrollmentUpdate
from src.api.schemas.enrollments import EnrollmentOut, EnrollmentCreateSchema, EnrollmentUpdateSchema


router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.get("/{enrollment_id}", response_model=EnrollmentOut)
async def get_enrollment(
    enrollment_id: EnrollmentID,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentUser
):
    return await enrollment_service.get(
        EnrollmentGet(
            id=enrollment_id,
            viewer_id=current_user
        )
    )
    

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=EnrollmentOut)
async def create_enrollment(
    enrollment: EnrollmentCreateSchema,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentUser
):
    return await enrollment_service.create(
        EnrollmentCreate(
            **enrollment.model_dump(),
            created_by=current_user
        )
    )
    
    
@router.patch("/{enrollment_id}/update-status", response_model=EnrollmentUpdateSchema)
async def update_status(
    enrollment_id: EnrollmentID,
    enrollment: EnrollmentUpdateSchema,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentUser
):
    
    return await enrollment_service.update(
        EnrollmentUpdate(
            id=enrollment_id,
            status=enrollment.status,
            expire_at=enrollment.expire_at,
            updated_by=current_user
        )
    )

    
@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enrollment(
    enrollment_id: EnrollmentID,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentUser
):
    
    return await enrollment_service.delete(
        EnrollmentDelete(
            id=enrollment_id,
            deleted_by=current_user
        )
    )
    


