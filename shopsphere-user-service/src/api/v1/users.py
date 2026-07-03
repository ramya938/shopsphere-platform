from fastapi import APIRouter, Depends, status
from src.api.schemas.user import UserResponse, UserUpdateRequest
from src.services.user_service import UserService
from src.api.deps import get_user_service, get_current_user, RoleChecker
from src.domain.models import User, UserRole

router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get profile details",
    description="Returns the profile information of the currently authenticated user."
)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update profile details",
    description="Allows the authenticated user to modify their email, name, or password."
)
async def update_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.update_user_profile(
        user_id=current_user.id,
        email=request.email,
        full_name=request.full_name,
        password=request.password
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Permanently deletes the currently authenticated user's account."
)
async def delete_account(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    await user_service.delete_user_account(user_id=current_user.id)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users",
    description="Retrieve a list of all registered users. Restricted to ADMIN users only."
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.list_users(skip=skip, limit=limit)
