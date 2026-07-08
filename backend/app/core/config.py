"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
