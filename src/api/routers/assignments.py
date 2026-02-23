from fastapi import APIRouter, status
from src.api.dependencies import AssignmentServiceDependency, CurrentUser
from src.commands.base import AssignmentID
from src.api.schemas.assignments import AssignmentCreateSchema, AssignmentUpdateSchema, AssignmentOut
from src.commands.assignments import AssignmentCreate, AssignmentUpdate, AssignmentDelete, AssignmentGetQuery, AssignmentUploadUrl


router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser
):
    
    return await assignment_service.get(
        AssignmentGetQuery(
            id=assignment_id,
            viewer_id=current_user
        )
    )
    
@router.post("/", response_model=AssignmentUploadUrl)
async def create_assignment(
    assignment_payload: AssignmentCreateSchema,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser
):
    print(f"Payload is {assignment_payload.model_dump_json(indent=4)}")
    
    return await assignment_service.init_assignment_create(
        file_cmd=assignment_payload.file_metadata,
        cmd=AssignmentCreate(
            **assignment_payload.assignment.model_dump(),
            created_by=current_user
        )
    )
    

@router.patch("/{assignment_id}/update-details", response_model=AssignmentUpdateSchema)
async def update_assignment(
    assignment_id: AssignmentID,
    assignment: AssignmentUpdateSchema,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser
):
    return await assignment_service.update(
        AssignmentUpdate(
            **assignment.model_dump(),
            updated_by=current_user,
            id=assignment_id
        )
    )
    
    

@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser
):
    
    return await assignment_service.delete(
        AssignmentDelete(
            id=assignment_id,
            deleted_by=current_user
        )
    )
    

# NOTE: Rearrange is not implemented. Will implement if requires.