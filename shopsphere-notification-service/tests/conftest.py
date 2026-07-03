import asyncio
import os
from unittest.mock import AsyncMock, patch
import pytest

# Force environment overrides for testing before importing settings or app
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

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
