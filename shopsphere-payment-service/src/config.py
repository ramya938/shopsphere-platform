from typing import Literal
from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    PROJECT_NAME: str = "ShopSphere Payment Service"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5436
    POSTGRES_DB: str = "shopsphere_payments"
    
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> str:
        if isinstance(v, str) and v:
            return v
        
        user = info.data.get("POSTGRES_USER", "postgres")
        password = info.data.get("POSTGRES_PASSWORD", "postgres")
        host = info.data.get("POSTGRES_HOST", "localhost")
        port = info.data.get("POSTGRES_PORT", 5436)
        db = info.data.get("POSTGRES_DB", "shopsphere_payments")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Security Settings (Shared secret with User Service)
    JWT_SECRET_KEY: str = "e83a0adbc87612f0e0c034a706b85bfa17c7689d023bfe4c4246830501867e91"
    ALGORITHM: str = "HS256"

    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()
