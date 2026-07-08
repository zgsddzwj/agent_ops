"""AgentOps API - main application module."""

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import alerts, benchmarks, evals, metrics, projects, security, traces
from app.core.config import settings
from app.core.database import async_session, check_database_health, engine, init_database
from app.core.middleware import ExceptionHandlerMiddleware
from app.services.ingest import seed_model_pricing

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# ─── Middleware (order: outermost first) ───

# Trusted host validation (prevent host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"],
)

# GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1024)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception handling (innermost, closest to routes) ───

_exception_handler = ExceptionHandlerMiddleware()


@app.middleware("http")
async def exception_middleware(request: Request, call_next):
    """Global exception handler middleware (singleton instance)."""
    return await _exception_handler(request, call_next)


# ─── Rate limiter ───

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_MAX_IPS = 10_000  # Prevent unbounded memory growth


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware using in-memory sliding window."""
    if not settings.rate_limit_enabled:
        return await call_next(request)

    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    key = f"rl:{client_ip}"
    now = time.time()
    window = settings.rate_limit_window
    max_requests = settings.rate_limit_requests

    # Periodic cleanup: if store is too large, evict all expired entries
    if len(_rate_limit_store) > _RATE_LIMIT_MAX_IPS:
        expired_keys = [
            k for k, timestamps in _rate_limit_store.items()
            if not timestamps or now - timestamps[-1] > window
        ]
        for k in expired_keys:
            del _rate_limit_store[k]

    # Sliding window: remove expired timestamps
    _rate_limit_store[key] = [
        t for t in _rate_limit_store[key] if now - t < window
    ]

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
