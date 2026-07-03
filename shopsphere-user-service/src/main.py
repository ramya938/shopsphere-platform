import time
import uuid
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config import settings
from src.core.logging import setup_logging
from src.core.exceptions import (
    BaseAppException,
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InvalidCredentialsException,
    TokenExpiredException,
    InvalidTokenException,
    PermissionDeniedException,
)
from src.api.v1.auth import router as auth_router
from src.api.v1.users import router as users_router

# Initialize logging configuration before FastAPI bootstrap
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade Clean Architecture User Microservice for ShopSphere AI.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Domain Exception Handlers ---

@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )

@app.exception_handler(EntityAlreadyExistsException)
async def entity_already_exists_handler(request: Request, exc: EntityAlreadyExistsException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message},
    )

@app.exception_handler(InvalidCredentialsException)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(TokenExpiredException)
async def token_expired_handler(request: Request, exc: TokenExpiredException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(InvalidTokenException)
async def invalid_token_handler(request: Request, exc: InvalidTokenException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(PermissionDeniedException)
async def permission_denied_handler(request: Request, exc: PermissionDeniedException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message},
    )

@app.exception_handler(BaseAppException)
async def base_app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message},
    )

# --- Structured Logging & Tracing Middleware ---

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    # Retrieve existing request correlation ID or generate a new one
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Contextualize all logs within this request block with the correlation ID
    with logger.contextualize(request_id=request_id):
        start_time = time.time()
        logger.info(f"Started Request: {request.method} {request.url.path}")
        try:
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"
            
            logger.info(
                f"Finished Request: {request.method} {request.url.path} "
                f"-> Status {response.status_code} in {process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.exception(
                f"Unhandled Exception in Request: {request.method} {request.url.path} "
                f"after {process_time:.4f}s. Error: {str(e)}"
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An unexpected error occurred. Please contact the administrator."},
            )

# --- Include Routers ---
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple service health probe."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}
