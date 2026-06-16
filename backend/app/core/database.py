import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=getattr(settings, "debug", False),
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_database() -> None:
    """Initialize database: create tables if they don't exist."""
    from app.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def check_database_health() -> bool:
    """Check if the database is reachable."""
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a transactional database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
