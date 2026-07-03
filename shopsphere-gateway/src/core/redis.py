import redis.asyncio as redis
from loguru import logger
from src.config import settings

class RedisManager:
    """Manages the lifecycle of Redis client connections."""
    def __init__(self, url: str = settings.REDIS_URL):
        self.url = url
        self.client: redis.Redis | None = None

    async def start(self):
        logger.info(f"Connecting to Redis at {self.url}...")
        self.client = redis.from_url(
            self.url,
            decode_responses=True,
            socket_timeout=5.0
        )
        # Test connection
        await self.client.ping()
        logger.info("Connected to Redis successfully.")

    async def stop(self):
        if self.client:
            logger.info("Closing Redis connection...")
            await self.client.close()
            logger.info("Redis connection closed.")

redis_manager = RedisManager()
