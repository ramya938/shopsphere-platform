from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database import AsyncSessionLocal
from src.infrastructure.repositories.category_repository import SQLAlchemyCategoryRepository
from src.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from src.services.category_service import CategoryService
from src.services.product_service import ProductService
from src.core import security
from src.core.exceptions import InvalidTokenException, TokenExpiredException

# Token scheme points to User Service auth URL on port 8000 for Swagger UI integration
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8000/api/v1/auth/login",
    auto_error=True
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

def get_category_repository(session: AsyncSession = Depends(get_db)) -> SQLAlchemyCategoryRepository:
    """Dependency provider for Category repository."""
    return SQLAlchemyCategoryRepository(session)

def get_product_repository(session: AsyncSession = Depends(get_db)) -> SQLAlchemyProductRepository:
    """Dependency provider for Product repository."""
    return SQLAlchemyProductRepository(session)

def get_category_service(
    category_repo: SQLAlchemyCategoryRepository = Depends(get_category_repository)
) -> CategoryService:
    """Dependency provider for CategoryService."""
    return CategoryService(category_repo)

def get_product_service(
    product_repo: SQLAlchemyProductRepository = Depends(get_product_repository),
    category_repo: SQLAlchemyCategoryRepository = Depends(get_category_repository)
) -> ProductService:
    """Dependency provider for ProductService."""
    return ProductService(product_repo, category_repo)

async def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Stateless JWT verification using the shared User Service key.
    Returns token payload (claims) if valid, otherwise raises HTTP 401.
    """
    try:
        return security.decode_token(token)
    except (InvalidTokenException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """
    FastAPI dependency factory to check user roles from JWT claims.
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, claims: dict = Depends(get_current_user_claims)) -> dict:
        role = claims.get("role")
        if not role or role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Insufficient permissions."
            )
        return claims
