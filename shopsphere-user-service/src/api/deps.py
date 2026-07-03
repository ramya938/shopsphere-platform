from typing import AsyncGenerator
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database import AsyncSessionLocal
from src.infrastructure.repositories.user_repository import SQLAlchemyUserRepository, SQLAlchemyRefreshTokenRepository
from src.services.user_service import UserService
from src.domain.models import User, UserRole
from src.core import security
from src.config import settings
from src.core.exceptions import InvalidTokenException, TokenExpiredException, EntityNotFoundException

# OAuth2 Password Bearer for OpenAPI and FastAPI dependency integration
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide an asynchronous SQLAlchemy session.
    Automatically commits changes at request completion, or rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_user_repository(session: AsyncSession = Depends(get_db)) -> SQLAlchemyUserRepository:
    """Dependency provider for the User repository."""
    return SQLAlchemyUserRepository(session)

def get_refresh_token_repository(session: AsyncSession = Depends(get_db)) -> SQLAlchemyRefreshTokenRepository:
    """Dependency provider for the RefreshToken repository."""
    return SQLAlchemyRefreshTokenRepository(session)

def get_user_service(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    token_repo: SQLAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository)
) -> UserService:
    """Dependency provider for the UserService."""
    return UserService(user_repo, token_repo)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    Dependency to authenticate and retrieve the current active user.
    Throws HTTP 401 on authentication failures.
    """
    try:
        # Decode and validate access token
        payload = security.decode_token(token, settings.JWT_SECRET_KEY)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_418_IM_A_TEAPOT, # Just a placeholder fallback for schema error
                detail="Token subject missing."
            )
        
        user_id = uuid.UUID(user_id_str)
        return await user_service.get_user_profile(user_id)
        
    except (InvalidTokenException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except EntityNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token not found or is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid identifier format in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """
    FastAPI dependency factory to enforce Role-Based Access Control (RBAC).
    """
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Insufficient permissions."
            )
        return current_user
