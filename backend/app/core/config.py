"""Application configuration loaded from environment variables."""

import logging
import warnings
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Centralized application settings.

    All fields can be overridden via environment variables or a .env file.
    Field names are case-insensitive (e.g. ``DEBUG=true`` sets ``debug``).
    """

    # ─── Database ───
    database_url: str = "postgresql+asyncpg://agentops:agentops@localhost:5432/agentops"
    database_url_sync: str = "postgresql://agentops:agentops@localhost:5432/agentops"

    # ─── Redis ───
    redis_url: str = "redis://localhost:6379/0"

    # ─── Security ───
    secret_key: str = "change-me-in-production"

    # ─── API ───
    cors_origins: str = "http://localhost:3000"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_requests: bool = False
    api_timeout: int = 30

    # ─── Rate Limiting ───
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # ─── Model config ───
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Warn if the default secret key is used in a non-debug environment."""
        if v == "change-me-in-production":
            warnings.warn(
                "Using default secret_key. Set SECRET_KEY environment variable "
                "to a secure random value for production deployment.",
                stacklevel=2,
            )
            logger.warning("Default secret_key is in use - not safe for production!")
        return v

    @field_validator("api_port")
    @classmethod
    def validate_api_port(cls, v: int) -> int:
        """Validate that the API port is within the valid range."""
        if not (1 <= v <= 65535):
            raise ValueError(f"api_port must be between 1 and 65535, got {v}")
        return v

    @field_validator("rate_limit_requests")
    @classmethod
    def validate_rate_limit_requests(cls, v: int) -> int:
        """Validate that rate_limit_requests is a positive integer."""
        if v <= 0:
            raise ValueError(f"rate_limit_requests must be positive, got {v}")
        return v

    @field_validator("rate_limit_window")
    @classmethod
    def validate_rate_limit_window(cls, v: int) -> int:
        """Validate that rate_limit_window is a positive integer."""
        if v <= 0:
            raise ValueError(f"rate_limit_window must be positive, got {v}")
        return v

    @field_validator("api_timeout")
    @classmethod
    def validate_api_timeout(cls, v: int) -> int:
        """Validate that api_timeout is a positive integer."""
        if v <= 0:
            raise ValueError(f"api_timeout must be positive, got {v}")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
