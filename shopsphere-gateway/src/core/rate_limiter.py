import time
import uuid
from loguru import logger
from src.core.redis import redis_manager

async def is_rate_limited(identifier: str, limit: int, window: int) -> bool:
    """
    Checks if a given identifier has exceeded the rate limit using a sliding window.
    """
    if not redis_manager.client:
        logger.error("Redis client is unavailable. Allowing request through rate limiter.")
        return False

    key = f"rate_limit:{identifier}"
    now = time.time()
    cutoff = now - window
    member_id = f"{now}-{uuid.uuid4().hex[:6]}"

    try:
        async with redis_manager.client.pipeline(transaction=True) as pipe:
            # Remove elements older than cutoff window
            pipe.zremrangebyscore(key, 0, cutoff)
            # Get current number of requests in this window
            pipe.zcard(key)
            # Add current request timestamp with a unique member ID
            pipe.zadd(key, {member_id: now})
            # Reset expiration to keep Redis clean
            pipe.expire(key, window)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # results[1] corresponds to zcard result (before adding current item)
            current_requests = results[1]
            if current_requests >= limit:
                logger.warning(f"Rate limit EXCEEDED for identifier: {identifier} ({current_requests}/{limit})")
                return True
                
            logger.debug(f"Rate limit OK for {identifier}: {current_requests + 1}/{limit}")
            return False
            
    except Exception as e:
        logger.error(f"Error executing rate limit check in Redis: {e}. Allowing request.")
        return False
