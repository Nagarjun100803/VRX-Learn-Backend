from fastapi import APIRouter, status

from src.api.dependencies import CurrentAdmin, EnrollmentServiceDependency
from src.api.docs.enrollments import (
    CREATE_ENROLLMENT,
    DELETE_ENROLLMENT,
    GET_ENROLLMENT,
    UPDATE_ENROLLMENT,
)
from src.api.schemas.enrollments import (
    EnrollmentCreateSchema,
    EnrollmentOut,
    EnrollmentUpdateSchema,
    RestrictedModuleIds,
)
from src.command.commands.base import EnrollmentID
from src.command.commands.enrollments import (
    EnrollmentCreateWithRestrictions,
    EnrollmentDelete,
    EnrollmentGet,
    EnrollmentModuleRestrictionSync,
    EnrollmentUpdate,
    EnrollmentWithRestriction,
)

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.get(
    "/{enrollment_id}", response_model=EnrollmentWithRestriction, **GET_ENROLLMENT
)
async def get_enrollment(
    enrollment_id: EnrollmentID,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentAdmin,
):
    return await enrollment_service.get_with_restriction(
        EnrollmentGet(id=enrollment_id, viewer_id=current_user)
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=EnrollmentOut,
    **CREATE_ENROLLMENT,
)
async def create_enrollment(
    enrollment: EnrollmentCreateSchema,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentAdmin,
):
    return await enrollment_service.create(
        EnrollmentCreateWithRestrictions(
            **enrollment.model_dump(), created_by=current_user
        )
    )


@router.patch(
    "/{enrollment_id}/update-status",
    response_model=EnrollmentUpdateSchema,
    **UPDATE_ENROLLMENT,
)
async def update_status(
    enrollment_id: EnrollmentID,
    enrollment: EnrollmentUpdateSchema,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentAdmin,
):

    return await enrollment_service.update(
        EnrollmentUpdate(
            id=enrollment_id,
            status=enrollment.status,
            expire_at=enrollment.expire_at,
            updated_by=current_user,
        )
    )


@router.patch(
    "/{enrollment_id}/sync-restriction", status_code=status.HTTP_204_NO_CONTENT
)
async def sync_module_restriction(
    enrollment_id: EnrollmentID,
    module_ids: RestrictedModuleIds,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentAdmin,
):
    await enrollment_service.sync_module_restriction(
        cmd=EnrollmentModuleRestrictionSync(
            enrollment_id=enrollment_id,
            module_ids=module_ids.module_ids,
            updated_by=current_user,
        )
    )


@router.delete(
    "/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_ENROLLMENT
)
async def delete_enrollment(
    enrollment_id: EnrollmentID,
    enrollment_service: EnrollmentServiceDependency,
    current_user: CurrentAdmin,
):

    return await enrollment_service.delete(
        EnrollmentDelete(id=enrollment_id, deleted_by=current_user)
    )
