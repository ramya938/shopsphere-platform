import asyncio
import os
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Force environment overrides for testing before importing settings or app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_LEVEL"] = "WARNING"

@pytest.fixture(scope="session", autouse=True)
def mock_kafka_infrastructure():
    # Patch AIOKafkaProducer and AIOKafkaConsumer globally during tests to isolate broker dependency
    with patch("aiokafka.AIOKafkaProducer.start", new_callable=AsyncMock), \
         patch("aiokafka.AIOKafkaProducer.stop", new_callable=AsyncMock), \
         patch("aiokafka.AIOKafkaProducer.send_and_wait", new_callable=AsyncMock), \
         patch("aiokafka.AIOKafkaConsumer.start", new_callable=AsyncMock), \
         patch("aiokafka.AIOKafkaConsumer.stop", new_callable=AsyncMock), \
         patch("aiokafka.AIOKafkaConsumer.getmany", new_callable=AsyncMock) as mock_getmany:
         
        mock_getmany.return_value = {}
        yield

from src.main import app
from src.config import settings
from src.domain.models import Base
from src.api.deps import get_db, get_product_client

# Create an async database engine for the in-memory SQLite database
test_engine = create_async_engine(settings.DATABASE_URL, future=True)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class MockProductClient:
    """Mock product client to isolate product service dependency in tests."""
    def __init__(self):
        self.products = {}

    def add_mock_product(self, product_id: uuid.UUID, name: str, price: float, inventory_quantity: int, status: str = "ACTIVE"):
        self.products[product_id] = {
            "id": str(product_id),
            "name": name,
            "price": price,
            "inventory_quantity": inventory_quantity,
            "status": status
        }

    async def get_product(self, product_id: uuid.UUID):
        return self.products.get(product_id)

    async def deduct_stock(self, product_id: uuid.UUID, quantity: int):
        p = self.products.get(product_id)
        if p and p["inventory_quantity"] >= quantity:
            p["inventory_quantity"] -= quantity
            return True
        return False

    async def restock_stock(self, product_id: uuid.UUID, quantity: int):
        p = self.products.get(product_id)
        if p:
            p["inventory_quantity"] += quantity
            return True
        return False


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def init_db():
    """Create database tables before tests and tear them down afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional database session for a single test.
    Automatically rolls back changes so tests remain isolated.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture(autouse=True)
def override_db_dependency(db_session: AsyncSession):
    """Override get_db with the transactional test session."""
    async def _get_db_override():
        yield db_session
    
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_product_client() -> MockProductClient:
    return MockProductClient()


@pytest.fixture(autouse=True)
def override_product_client(mock_product_client):
    app.dependency_overrides[get_product_client] = lambda: mock_product_client
    yield
    if get_product_client in app.dependency_overrides:
        del app.dependency_overrides[get_product_client]


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client to call endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def admin_headers() -> dict:
    """Returns headers with a signed Admin JWT token."""
    payload = {
        "sub": "a9b8c7d6-e5f4-3c2b-1a09-876543210fed",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_headers() -> dict:
    """Returns headers with a signed Customer JWT token."""
    payload = {
        "sub": "b2c3d4e5-f6a7-0b1c-2d3e-4f5a6b7c8d9e",
        "role": "CUSTOMER",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_customer_headers() -> dict:
    """Returns headers with another Customer JWT token."""
    payload = {
        "sub": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
        "role": "CUSTOMER",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}
