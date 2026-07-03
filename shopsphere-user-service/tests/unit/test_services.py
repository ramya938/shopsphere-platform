import pytest
import uuid
from datetime import datetime, timedelta, timezone
from src.services.user_service import UserService
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository, SQLAlchemyRefreshTokenRepository
from src.domain.models import UserRole
from src.core.exceptions import (
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException
)

@pytest.fixture
def user_service(db_session) -> UserService:
    user_repo = SQLAlchemyUserRepository(db_session)
    token_repo = SQLAlchemyRefreshTokenRepository(db_session)
    return UserService(user_repo, token_repo)


@pytest.mark.asyncio
async def test_register_user_success(user_service):
    """Verify successful user registration and password hashing."""
    user = await user_service.register_user(
        email="register_success@shopsphere.ai",
        password="securePassword123",
        full_name="Register Test"
    )
    assert user.id is not None
    assert user.email == "register_success@shopsphere.ai"
    assert user.full_name == "Register Test"
    assert user.role == UserRole.CUSTOMER
    assert user.hashed_password != "securePassword123" # Must be hashed!


@pytest.mark.asyncio
async def test_register_user_duplicate_email(user_service):
    """Verify registration fails with duplicate email address."""
    await user_service.register_user(
        email="duplicate@shopsphere.ai",
        password="securePassword123",
        full_name="User One"
    )
    
    with pytest.raises(EntityAlreadyExistsException):
        await user_service.register_user(
            email="duplicate@shopsphere.ai",
            password="anotherPassword456",
            full_name="User Two"
        )


@pytest.mark.asyncio
async def test_authenticate_user_success(user_service):
    """Verify user can authenticate with correct credentials and receive tokens."""
    email = "auth_success@shopsphere.ai"
    password = "authPassword123"
    await user_service.register_user(
        email=email,
        password=password,
        full_name="Auth Success"
    )
    
    access_token, refresh_token, user = await user_service.authenticate_user(email, password)
    assert access_token is not None
    assert refresh_token is not None
    assert user.email == email


@pytest.mark.asyncio
async def test_authenticate_user_failure(user_service):
    """Verify authentication fails for non-existent users and bad passwords."""
    email = "auth_fail@shopsphere.ai"
    password = "correctPassword123"
    await user_service.register_user(
        email=email,
        password=password,
        full_name="Auth Fail"
    )
    
    # Test incorrect password
    with pytest.raises(InvalidCredentialsException):
        await user_service.authenticate_user(email, "wrongPassword")
        
    # Test non-existent email
    with pytest.raises(InvalidCredentialsException):
        await user_service.authenticate_user("not_exists@shopsphere.ai", password)


@pytest.mark.asyncio
async def test_update_profile_success(user_service):
    """Verify profile fields are updated successfully."""
    user = await user_service.register_user(
        email="update@shopsphere.ai",
        password="password123",
        full_name="Update Before"
    )
    
    updated = await user_service.update_user_profile(
        user_id=user.id,
        email="update_new@shopsphere.ai",
        full_name="Update After"
    )
    
    assert updated.email == "update_new@shopsphere.ai"
    assert updated.full_name == "Update After"


@pytest.mark.asyncio
async def test_update_profile_email_collision(user_service):
    """Verify profile email update fails if target email is already taken."""
    user_one = await user_service.register_user(
        email="one@shopsphere.ai", password="password123", full_name="User One"
    )
    user_two = await user_service.register_user(
        email="two@shopsphere.ai", password="password123", full_name="User Two"
    )
    
    with pytest.raises(EntityAlreadyExistsException):
        await user_service.update_user_profile(
            user_id=user_one.id,
            email="two@shopsphere.ai"
        )


@pytest.mark.asyncio
async def test_delete_user_account(user_service):
    """Verify account deletion deletes user and fails on non-existent users."""
    user = await user_service.register_user(
        email="delete@shopsphere.ai", password="password123", full_name="Delete Me"
    )
    
    await user_service.delete_user_account(user.id)
    
    with pytest.raises(EntityNotFoundException):
        await user_service.get_user_profile(user.id)
        
    # Deleting again must fail
    with pytest.raises(EntityNotFoundException):
        await user_service.delete_user_account(user.id)
