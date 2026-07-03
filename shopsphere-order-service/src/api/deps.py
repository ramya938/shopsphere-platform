from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database import AsyncSessionLocal
from src.infrastructure.repositories.cart_repository import SQLAlchemyCartRepository
from src.infrastructure.repositories.order_repository import SQLAlchemyOrderRepository
from src.infrastructure.clients.product_client import ProductClient
from src.services.cart_service import CartService
from src.services.order_service import OrderService
from src.core import security
from src.core.exceptions import InvalidTokenException, TokenExpiredException
import httpx
from src.core.kafka import KafkaProducerManager

# Shared HTTP client for microservice communications
_http_client = httpx.AsyncClient(timeout=10.0)

async def get_http_client() -> httpx.AsyncClient:
    return _http_client

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8000/api/v1/auth/login",
    auto_error=True
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to yield database sessions, automatically committing or rolling back."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_product_client(client: httpx.AsyncClient = Depends(get_http_client)) -> ProductClient:
    return ProductClient(client=client)

def get_cart_repository(session: AsyncSession = Depends(get_db)) -> SQLAlchemyCartRepository:
    return SQLAlchemyCartRepository(session)

def get_order_repository(session: AsyncSession = Depends(get_db)) -> SQLAlchemyOrderRepository:
    return SQLAlchemyOrderRepository(session)

def get_cart_service(
    cart_repo: SQLAlchemyCartRepository = Depends(get_cart_repository),
    product_client: ProductClient = Depends(get_product_client)
) -> CartService:
    return CartService(cart_repo=cart_repo, product_client=product_client)

_kafka_producer = KafkaProducerManager()

def get_kafka_producer() -> KafkaProducerManager:
    return _kafka_producer

def get_order_service(
    order_repo: SQLAlchemyOrderRepository = Depends(get_order_repository),
    cart_repo: SQLAlchemyCartRepository = Depends(get_cart_repository),
    product_client: ProductClient = Depends(get_product_client),
    producer_manager: KafkaProducerManager = Depends(get_kafka_producer)
) -> OrderService:
    return OrderService(
        order_repo=order_repo,
        cart_repo=cart_repo,
        product_client=product_client,
        producer_manager=producer_manager
    )

async def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> dict:
    """Stateless verification of JWT token, returning claims dict."""
    try:
        claims = security.decode_token(token)
        if claims.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return claims
    except (InvalidTokenException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """Dependency checking if the caller possesses allowed role levels."""
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
