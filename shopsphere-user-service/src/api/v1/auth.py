from fastapi import APIRouter, Depends, status
from src.api.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from src.api.schemas.user import UserResponse
from src.services.user_service import UserService
from src.api.deps import get_user_service

router = APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user profile with CUSTOMER role by default. Admin access requires administrative privileges."
)
async def register(
    request: RegisterRequest,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and retrieve tokens",
    description="Verify credentials and generate JWT Access and Refresh tokens."
)
async def login(
    request: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    access_token, refresh_token, _ = await user_service.authenticate_user(
        email=request.email,
        password=request.password
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate tokens",
    description="Provide a valid refresh token to rotate both access and refresh tokens."
)
async def refresh(
    request: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
):
    access_token, refresh_token = await user_service.refresh_tokens(
        refresh_token_str=request.refresh_token
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
