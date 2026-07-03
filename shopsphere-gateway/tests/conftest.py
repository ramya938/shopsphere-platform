import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import patch
import pytest
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport

# Force environment overrides for testing before importing settings or app
os.environ["ENVIRONMENT"] = "testing"
os.environ["REDIS_URL"] = "redis://localhost:6379/9"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["USER_SERVICE_URL"] = "http://user-service:8000"
os.environ["PRODUCT_SERVICE_URL"] = "http://product-service:8001"
os.environ["ORDER_SERVICE_URL"] = "http://order-service:8002"

@pytest.fixture(scope="session", autouse=True)
def mock_redis_connection():
    # Use fakeredis to mock Redis in-memory
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    from src.core.redis import redis_manager
    redis_manager.client = fake_client
    with patch("redis.asyncio.from_url", return_value=fake_client):
        yield fake_client

from src.main import app
from src.config import settings

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client to call the gateway."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://gatewaytest") as async_client:
        yield async_client
