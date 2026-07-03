import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
import pytest
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
