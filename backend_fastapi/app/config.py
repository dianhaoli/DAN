"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql://localhost:5432/dan"

    # Redis (for Celery + rate limiting)
    redis_url: str = "redis://localhost:6379/0"

    # Firebase
    firebase_project_id: str = ""
    firebase_credentials_path: Optional[str] = None

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # Rate Limits
    rate_limit_general: int = 100  # requests per minute
    rate_limit_ai: int = 20  # requests per hour

    # ML
    ml_models_path: str = "./ml_models"
    ml_thread_pool_size: int = 4

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
