import time
import uuid
import httpx
import jwt
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config import settings
from src.core.logging import setup_logging
from src.core.redis import redis_manager
from src.core.jwt_validator import validate_jwt, get_auth_token
from src.core.rate_limiter import is_rate_limited
from src.core.caching import get_cached_response, set_cached_response

# Configure logger before app bootstrap
setup_logging()

# Global long-lived HTTPX client instance
_http_client = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
        _http_client = httpx.AsyncClient(limits=limits, timeout=15.0)
    return _http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client
    # 1. Connect to Redis
    try:
        await redis_manager.start()
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")

    # 2. Initialize HTTPX client pool
    get_http_client()
    logger.info("HTTPX Client Pool initialized.")
    
    yield
    
    # Shutdown:
    # 1. Close HTTPX client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
        logger.info("HTTPX Client Pool closed.")
        
    # 2. Disconnect from Redis
    await redis_manager.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade Custom API Gateway microservice for ShopSphere AI.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed dependencies health check probe."""
    health_status = {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "dependencies": {
            "redis": "unhealthy",
            "user_service": "unhealthy",
            "product_service": "unhealthy",
            "order_service": "unhealthy"
        }
    }
    
    # Check Redis
    if redis_manager.client:
        try:
            await redis_manager.client.ping()
            health_status["dependencies"]["redis"] = "healthy"
        except Exception:
            health_status["status"] = "degraded"
            
    # Asynchronous check helper for downstreams
    async def check_service(url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{url}/health")
                if res.status_code == 200:
                    return "healthy"
        except Exception:
            pass
        return "unhealthy"
        
    health_status["dependencies"]["user_service"] = await check_service(settings.USER_SERVICE_URL)
    health_status["dependencies"]["product_service"] = await check_service(settings.PRODUCT_SERVICE_URL)
    health_status["dependencies"]["order_service"] = await check_service(settings.ORDER_SERVICE_URL)
    
    if any(status == "unhealthy" for status in health_status["dependencies"].values()):
        if health_status["status"] != "degraded":
            health_status["status"] = "degraded"
            
    if all(status == "unhealthy" for status in health_status["dependencies"].values()):
        health_status["status"] = "unhealthy"
        
    status_code = status.HTTP_200_OK
    if health_status["status"] == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return JSONResponse(status_code=status_code, content=health_status)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def gateway_route_proxy(request: Request, path: str):
    """Catch-all proxy router forwarding requests downstream."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    with logger.contextualize(request_id=request_id):
        # 1. Resolve Downstream Service URL
        clean_path = path.lstrip("/")
        
        if clean_path.startswith("api/v1/auth") or clean_path.startswith("api/v1/users"):
            target_service_url = settings.USER_SERVICE_URL
        elif clean_path.startswith("api/v1/categories") or clean_path.startswith("api/v1/products"):
            target_service_url = settings.PRODUCT_SERVICE_URL
        elif clean_path.startswith("api/v1/cart") or clean_path.startswith("api/v1/orders"):
            target_service_url = settings.ORDER_SERVICE_URL
        else:
            logger.warning(f"Route not found in API Gateway: {request.method} /{path}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Route not found in API Gateway: {request.method} /{path}"}
            )

        # 2. JWT Verification and Claims Extraction
        user_id = None
        user_role = None
        auth_header = request.headers.get("Authorization")
        token = get_auth_token(auth_header)
        
        if token:
            try:
                payload = validate_jwt(token)
                user_id = payload.get("sub")
                user_role = payload.get("role")
                logger.info(f"JWT validated. User: {user_id}, Role: {user_role}")
            except jwt.ExpiredSignatureError:
                logger.info("JWT token validation failed: Expired signature.")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has expired"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            except jwt.PyJWTError as e:
                logger.info(f"JWT token validation failed: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

        # 3. Rate Limiter Checks
        if user_id:
            rate_limit_id = f"user:{user_id}"
            limit = settings.RATE_LIMIT_AUTH
        else:
            client_ip = request.client.host if request.client else "unknown_ip"
            rate_limit_id = f"ip:{client_ip}"
            limit = settings.RATE_LIMIT_ANON

        rate_limit_window = settings.RATE_LIMIT_WINDOW
        is_limited = await is_rate_limited(rate_limit_id, limit, rate_limit_window)
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(rate_limit_window)}
            )

        # 4. Check Redis Cache
        cached_response = await get_cached_response(request)
        if cached_response:
            return cached_response

        # 5. Formulate Request to Downstream Service
        target_url = f"{target_service_url}/{clean_path}"
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"

        body = await request.body()
        
        # Build headers dictionary and inject user attributes
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["X-Request-ID"] = request_id
        
        if user_id:
            headers["X-User-Id"] = str(user_id)
            headers["X-User-Role"] = str(user_role)

        logger.info(f"Proxying request: {request.method} /{clean_path} -> {target_url}")

        # 6. Dispatch Request to Downstream
        try:
            response = await get_http_client().request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=True
            )
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Downstream Connection error to {target_url}: {exc}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Service is temporarily unavailable."}
            )

        # 7. Write to cache if cacheable
        if response.status_code == 200:
            await set_cached_response(request, response.content, response.status_code, dict(response.headers))

        # 8. Return response
        response_headers = dict(response.headers)
        response_headers.pop("content-length", None)
        response_headers["X-Request-ID"] = request_id
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers
        )
