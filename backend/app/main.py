import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, benchmarks, evals, metrics, projects, security, traces
from app.core.config import settings
from app.core.database import async_session, check_database_health, engine, init_database
from app.models import Base
from app.services.ingest import seed_model_pricing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with structured startup/shutdown."""
    logger.info("Starting up AgentOps API...")
    try:
        await init_database()
        async with async_session() as db:
            await seed_model_pricing(db)
            await db.commit()
        logger.info("AgentOps API startup completed successfully")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info("Shutting down AgentOps API...")
        await engine.dispose()
        logger.info("AgentOps API shutdown completed")


app = FastAPI(title="AgentOps API", version="0.1.0", lifespan=lifespan)

# Add custom exception handling middleware
from app.core.middleware import ExceptionHandlerMiddleware

async def exception_middleware(request, call_next):
    handler = ExceptionHandlerMiddleware()
    return await handler(request, call_next)

app.middleware("http")(exception_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(traces.router)
app.include_router(metrics.router)
app.include_router(evals.router)
app.include_router(benchmarks.router)
app.include_router(security.router)
app.include_router(alerts.router)


@app.get("/health")
async def health():
    """Health check endpoint that validates database and Redis connectivity."""
    start_time = time.time()

    health_status = {
        "status": "ok",
        "service": "agent-ops-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Check database connectivity
    db_healthy = await check_database_health()
    health_status["database"] = "connected" if db_healthy else "disconnected"
    if not db_healthy:
        health_status["status"] = "degraded"

    # Check Redis connectivity
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        health_status["redis"] = "connected"
        await redis_client.aclose()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        health_status["redis"] = "disconnected"

    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    return health_status
