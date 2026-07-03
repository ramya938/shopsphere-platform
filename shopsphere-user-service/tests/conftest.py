import asyncio
import os
from typing import AsyncGenerator
import pytest
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
