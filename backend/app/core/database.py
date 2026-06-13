import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create async engine with connection pooling and proper configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
