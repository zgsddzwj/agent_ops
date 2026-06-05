from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, benchmarks, evals, metrics, projects, security, traces
from app.core.config import settings
from app.core.database import async_session, engine
from app.models import Base
from app.services.ingest import seed_model_pricing


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        await seed_model_pricing(db)
        await db.commit()
    yield
    await engine.dispose()


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
    return {"status": "ok", "service": "agent-ops-api"}
