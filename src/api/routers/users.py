from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from src.commands.base import UserID
from src.commands.users import UserGetByIDQuery, UserCreateWithConfirmPassword, UserDelete, UserAuth
from src.api.dependencies import UserServiceDependency, CurrentUser, JWTServiceDependency
from src.api.schemas.users import UserCreateSchema, UserOutSchema, LoginSchema
from src.api.jwt import JWTPayloadCreate


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/login")
async def login(
    login_details: LoginSchema,
    user_service: UserServiceDependency,
    jwt_service: JWTServiceDependency
):
    
    # Get user.
    user = await user_service.authenticate(
        UserAuth(
            email=login_details.email,
            password=login_details.password
        )
    )
    
    # Add a token in cookie and return.
    token = jwt_service.create_jwt_token(
        payload=JWTPayloadCreate(
            user_id=user.id,
            role=user.role
        )
    )
    response = JSONResponse(content={"message": "Logged in successfully"})
    response.set_cookie(
        key="access_token",
        value=token,
        samesite="lax",
        httponly=True
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logged out successfully."})
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    return response



@router.get("/{user_id}", response_model=UserOutSchema)
async def get_user(
    user_id: UserID,
    user_service: UserServiceDependency,
    current_user: CurrentUser
):
    return await user_service.get(        
        UserGetByIDQuery(
            id=user_id,
            viewer_id=current_user
        )
    )
    


@router.post("/", response_model=UserOutSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreateSchema,
    user_service: UserServiceDependency,
    current_user: CurrentUser
):
    
    return await user_service.create(
        UserCreateWithConfirmPassword(
            **user.model_dump(),
            created_by=current_user
        )
    )



@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UserID,
    user_service: UserServiceDependency,
    current_user: CurrentUser
):
    await user_service.delete(
        UserDelete(
            id=user_id,
            deleted_by=current_user
        )
    )
    