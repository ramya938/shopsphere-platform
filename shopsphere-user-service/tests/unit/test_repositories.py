import pytest
from datetime import datetime, timedelta, timezone
from src.domain.models import User, RefreshToken, UserRole
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository, SQLAlchemyRefreshTokenRepository

@pytest.mark.asyncio
async def test_user_repository_crud(db_session):
    """Verify CRUD operations on user repository."""
    repo = SQLAlchemyUserRepository(db_session)
    
    # Create User
    user = User(
        email="test_repo@shopsphere.ai",
        hashed_password="mock_hashed_password",
        full_name="Repository Tester",
        role=UserRole.CUSTOMER
    )
    saved = await repo.add(user)
    assert saved.id is not None
    assert saved.email == "test_repo@shopsphere.ai"
    assert saved.role == UserRole.CUSTOMER
    
    # Retrieve User by ID
    fetched_by_id = await repo.get_by_id(saved.id)
    assert fetched_by_id is not None
    assert fetched_by_id.email == "test_repo@shopsphere.ai"
    assert fetched_by_id.full_name == "Repository Tester"
    
    # Retrieve User by Email
    fetched_by_email = await repo.get_by_email("test_repo@shopsphere.ai")
    assert fetched_by_email is not None
    assert fetched_by_email.id == saved.id
    
    # List users
    all_users = await repo.list_all()
    assert len(all_users) >= 1
    
    # Update User profile
    saved.full_name = "Updated Repo Tester"
    updated = await repo.update(saved)
    assert updated.full_name == "Updated Repo Tester"
    
    # Delete User
    await repo.delete(saved)
    fetched_after_delete = await repo.get_by_id(saved.id)
    assert fetched_after_delete is None


@pytest.mark.asyncio
async def test_refresh_token_repository(db_session):
    """Verify operations on refresh token repository."""
    user_repo = SQLAlchemyUserRepository(db_session)
    token_repo = SQLAlchemyRefreshTokenRepository(db_session)
    
    # Insert User first to respect DB foreign key constraints
    user = User(
        email="token_repo_test@shopsphere.ai",
        hashed_password="mock_hashed_password",
        full_name="Token Tester"
    )
    saved_user = await user_repo.add(user)
    
    # Add Refresh Token
    token_str = "shopsphere_jwt_refresh_token_sample"
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = RefreshToken(
        user_id=saved_user.id,
        token=token_str,
        expires_at=expires
    )
    saved_token = await token_repo.add(refresh_token)
    assert saved_token.id is not None
    assert saved_token.user_id == saved_user.id
    
    # Retrieve Refresh Token by string
    fetched = await token_repo.get_by_token(token_str)
    assert fetched is not None
    assert fetched.user_id == saved_user.id
    assert fetched.token == token_str
    
    # Revoke/Delete all refresh tokens for user
    await token_repo.revoke_all_for_user(saved_user.id)
    fetched_after_revoke = await token_repo.get_by_token(token_str)
    assert fetched_after_revoke is None
