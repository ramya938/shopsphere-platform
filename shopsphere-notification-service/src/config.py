from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    PROJECT_NAME: str = "ShopSphere Notification Service"
    API_V1_STR: str = "/api/v1"

    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Security Settings (Shared secret with User Service)
    JWT_SECRET_KEY: str = "e83a0adbc87612f0e0c034a706b85bfa17c7689d023bfe4c4246830501867e91"
    ALGORITHM: str = "HS256"

    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()
