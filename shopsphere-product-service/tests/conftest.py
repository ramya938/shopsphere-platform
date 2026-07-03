import asyncio
import os
from typing import AsyncGenerator
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Force environment overrides for testing before importing settings or app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_LEVEL"] = "WARNING"

from src.main import app
from src.config import settings
from src.domain.models import Base
from src.api.deps import get_db

# Create an async database engine for the in-memory SQLite database
test_engine = create_async_engine(settings.DATABASE_URL, future=True)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

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
        "type": "access"
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
        "type": "access"
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}
