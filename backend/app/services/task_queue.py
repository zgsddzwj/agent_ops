"""Shared task queue utilities for enqueuing background jobs via ARQ/Redis."""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def enqueue_task(task_name: str, payload: dict) -> bool:
    """Enqueue a background task to Redis with proper error handling and logging.

    This is the centralized task enqueue function used by all route modules.
    It handles Redis connection lifecycle and provides structured logging
    for both success and failure cases.

    Args:
        task_name: Name of the ARQ task function to enqueue
        payload: Dictionary of task payload data

    Returns:
        True if task was enqueued successfully, False otherwise
    """
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job(task_name, payload)
        await redis.close()

        logger.info(
            "Task enqueued successfully",
            extra={
                "task_name": task_name,
                "job_id": str(job) if job else None,
            },
        )
        return True

    except ImportError:
        logger.debug("ARQ not available, task will not be enqueued")
        return False
    except Exception as exc:
        logger.warning(
            "Failed to enqueue task",
            extra={
                "task_name": task_name,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        return False
