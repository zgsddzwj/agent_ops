from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://agentops:agentops@localhost:5432/agentops"
    database_url_sync: str = "postgresql://agentops:agentops@localhost:5432/agentops"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
