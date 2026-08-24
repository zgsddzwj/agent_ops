"""Database engine, session factory, and health-check utilities."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
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
    """Check if the database is reachable by executing a simple SELECT 1.
    
    Returns:
        True if the database is reachable, False otherwise.
    """
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed (SQLAlchemy error): {e}")
        return False
    except Exception as e:
        logger.error(f"Database health check failed (unexpected error): {e}")
        return False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a transactional database session.
    
    Yields an AsyncSession and automatically commits on success.
    On exception, rolls back the transaction and re-raises.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database session error (SQLAlchemy): {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error (unexpected): {e}")
            raise
