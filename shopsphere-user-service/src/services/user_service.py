from datetime import datetime, timedelta, timezone
import uuid
from typing import Sequence
from loguru import logger
from src.domain.models import User, RefreshToken, UserRole
from src.domain.repository_interfaces import UserRepositoryInterface, RefreshTokenRepositoryInterface
from src.core import security
from src.core.exceptions import (
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException
)
from src.config import settings

class UserService:
    """
    Application Service orchestrating business workflows for the User domain.
    Decoupled from FastAPI routers and database-specific logic.
    """
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        refresh_token_repo: RefreshTokenRepositoryInterface
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def register_user(
        self, email: str, password: str, full_name: str, role: UserRole = UserRole.CUSTOMER
    ) -> User:
        """Register a new user in the system."""
        logger.info(f"Attempting to register user: {email}")
        
        # Check if email is already registered
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed: User with email {email} already exists")
            raise EntityAlreadyExistsException("A user with this email address already exists.")

        hashed_password = security.get_password_hash(password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True
        )
        
        saved_user = await self.user_repo.add(new_user)
        logger.info(f"User registered successfully: {saved_user.id} ({saved_user.role})")
        return saved_user

    async def authenticate_user(self, email: str, password: str) -> tuple[str, str, User]:
        """Authenticate user, return Access Token, Refresh Token, and User profile."""
        logger.info(f"Authentication attempt for user: {email}")
        
        user = await self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            logger.warning(f"Authentication failed: User {email} not found or inactive")
            raise InvalidCredentialsException("Invalid email or password")

        if not security.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Incorrect password for user {email}")
            raise InvalidCredentialsException("Invalid email or password")

        # Generate access and refresh tokens
        access_token = security.create_access_token(subject=user.id, role=user.role.value)
        refresh_token = security.create_refresh_token(subject=user.id)

        # Store the refresh token in database for rotation / revocation validation
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at
        )
        await self.refresh_token_repo.add(db_refresh_token)

        logger.info(f"User authenticated successfully: {user.id}")
        return access_token, refresh_token, user

    async def refresh_tokens(self, refresh_token_str: str) -> tuple[str, str]:
        """Validate refresh token and issue new Access Token and rotated Refresh Token."""
        logger.info("Token refresh request received")
        
        # 1. Decode token and verify type
        payload = security.decode_token(refresh_token_str, settings.JWT_REFRESH_SECRET_KEY)
        if payload.get("type") != "refresh":
            raise InvalidTokenException("Invalid token type")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenException("Invalid token payload")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise InvalidTokenException("Invalid identifier format in token")

        # 2. Check token existence, revocation, and expiration in DB
        db_token = await self.refresh_token_repo.get_by_token(refresh_token_str)
        if not db_token or db_token.is_revoked:
            logger.warning(f"Token refresh failed: token for user {user_id_str} is invalid or revoked in database")
            raise InvalidTokenException("Invalid, expired, or revoked refresh token")

        # Handle naive vs aware datetime comparison for SQLite vs PostgreSQL compatibility
        db_expires = db_token.expires_at
        is_expired = (
            db_expires < datetime.now(timezone.utc)
            if db_expires.tzinfo is not None
            else db_expires < datetime.now(timezone.utc).replace(tzinfo=None)
        )
        if is_expired:
            logger.warning(f"Token refresh failed: token for user {user_id_str} has expired")
            raise InvalidTokenException("Invalid, expired, or revoked refresh token")

        # 3. Security best practice: Revoke the current refresh token (rotation)
        db_token.is_revoked = True

        # 4. Generate new tokens
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenException("User associated with refresh token is inactive or not found")
        new_access_token = security.create_access_token(subject=user_id, role=user.role.value)
        new_refresh_token = security.create_refresh_token(subject=user_id)

        # 5. Save new refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_db_token = RefreshToken(
            user_id=user_id,
            token=new_refresh_token,
            expires_at=expires_at
        )
        await self.refresh_token_repo.add(new_db_token)

        logger.info(f"Tokens rotated successfully for user: {user_id}")
        return new_access_token, new_refresh_token

    async def get_user_profile(self, user_id: uuid.UUID) -> User:
        """Get the profile of a user by UUID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise EntityNotFoundException("User not found or is inactive")
        return user

    async def update_user_profile(
        self,
        user_id: uuid.UUID,
        email: str | None = None,
        full_name: str | None = None,
        password: str | None = None
    ) -> User:
        """Update a user's profile information."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise EntityNotFoundException("User not found")

        if email and email != user.email:
            # Check email duplication
            existing = await self.user_repo.get_by_email(email)
            if existing:
                raise EntityAlreadyExistsException("This email address is already in use by another account.")
            user.email = email

        if full_name:
            user.full_name = full_name

        if password:
            user.hashed_password = security.get_password_hash(password)

        updated_user = await self.user_repo.update(user)
        logger.info(f"User profile updated successfully: {user_id}")
        return updated_user

    async def delete_user_account(self, user_id: uuid.UUID) -> None:
        """Hard delete a user from the system."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User not found")
        
        await self.user_repo.delete(user)
        logger.info(f"User account deleted successfully: {user_id}")

    async def list_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Retrieve a paginated list of users (Admin operation)."""
        logger.info(f"Listing users: skip={skip}, limit={limit}")
        return await self.user_repo.list_all(skip=skip, limit=limit)
