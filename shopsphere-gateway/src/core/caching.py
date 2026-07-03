import json
import hashlib
from fastapi import Request, Response
from loguru import logger
from src.core.redis import redis_manager
from src.config import settings

def is_cacheable(request: Request) -> bool:
    """Only GET requests on products and categories catalog endpoints are cacheable."""
    if request.method != "GET":
        return False
    path = request.url.path
    return path.startswith("/api/v1/products") or path.startswith("/api/v1/categories")

def get_cache_key(request: Request) -> str:
    """Generates a unique deterministic cache key based on URL and sorted query parameters."""
    query_params = sorted(request.query_params.items())
    query_str = "&".join(f"{k}={v}" for k, v in query_params)
    raw_key = f"{request.url.path}?{query_str}"
    key_hash = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
    return f"gateway_cache:{key_hash}"

async def get_cached_response(request: Request) -> Response | None:
    if not is_cacheable(request) or not redis_manager.client:
        return None

    key = get_cache_key(request)
    try:
        cached_data = await redis_manager.client.get(key)
        if cached_data:
            logger.info(f"Cache HIT for key: {key}")
            data = json.loads(cached_data)
            return Response(
                content=data["body"],
                status_code=data["status_code"],
                media_type=data.get("media_type", "application/json"),
                headers={"X-Cache": "HIT"}
            )
    except Exception as e:
        logger.warning(f"Error fetching from Redis cache: {e}")
    return None

async def set_cached_response(request: Request, response_content: bytes, status_code: int, headers: dict):
    if not is_cacheable(request) or not redis_manager.client or status_code != 200:
        return

    key = get_cache_key(request)
    media_type = headers.get("content-type", "application/json")
    
    # Store minimal response parameters
    data = {
        "status_code": status_code,
        "body": response_content.decode("utf-8", errors="ignore"),
        "media_type": media_type
    }
    try:
        await redis_manager.client.setex(
            key,
            settings.CACHE_TTL_SECONDS,
            json.dumps(data)
        )
        logger.info(f"Cache SET for key: {key} (TTL: {settings.CACHE_TTL_SECONDS}s)")
    except Exception as e:
        logger.warning(f"Error writing to Redis cache: {e}")
