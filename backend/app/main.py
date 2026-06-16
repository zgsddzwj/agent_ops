import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import alerts, benchmarks, evals, metrics, projects, security, traces
from app.core.config import settings
from app.core.database import async_session, check_database_health, engine, init_database
from app.models import Base
from app.services.ingest import seed_model_pricing

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


app = FastAPI(
    title="AgentOps API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if getattr(settings, "debug", False) else None,
    redoc_url="/redoc" if getattr(settings, "debug", False) else None,
    openapi_url="/openapi.json" if getattr(settings, "debug", False) else None,
)


# ─── Exception handling middleware ───

from app.core.middleware import ExceptionHandlerMiddleware


@app.middleware("http")
async def exception_middleware(request: Request, call_next):
    handler = ExceptionHandlerMiddleware()
    return await handler(request, call_next)


# ─── Simple in-process rate limiter ───

_rate_limit_store: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware using in-memory sliding window."""
    if not getattr(settings, "rate_limit_enabled", False):
        return await call_next(request)

    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    key = f"rl:{client_ip}"
    now = time.time()
    window = getattr(settings, "rate_limit_window", 60)
    max_requests = getattr(settings, "rate_limit_requests", 100)

    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    # Remove expired entries
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < window]

    if len(_rate_limit_store[key]) >= max_requests:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests",
                "detail": f"Rate limit: {max_requests} requests per {window}s",
            },
        )

    _rate_limit_store[key].append(now)
    return await call_next(request)


# ─── CORS middleware ───

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routes ───

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
