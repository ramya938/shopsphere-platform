from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    PROJECT_NAME: str = "ShopSphere API Gateway"
    LOG_LEVEL: str = "INFO"

    # JWT Config (shared secret)
    JWT_SECRET_KEY: str = "e83a0adbc87612f0e0c034a706b85bfa17c7689d023bfe4c4246830501867e91"
    ALGORITHM: str = "HS256"

    # Redis Config
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 60

    # Rate Limiting (default 60 seconds sliding window)
    RATE_LIMIT_WINDOW: int = 60
    RATE_LIMIT_AUTH: int = 100
    RATE_LIMIT_ANON: int = 20

    # Microservice Route Targets
    USER_SERVICE_URL: str = "http://localhost:8010"
    PRODUCT_SERVICE_URL: str = "http://localhost:8011"
    ORDER_SERVICE_URL: str = "http://localhost:8012"

settings = Settings()
