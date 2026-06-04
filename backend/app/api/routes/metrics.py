from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.database import get_db
from app.models import Project
from app.schemas import MetricsSummary, TimeseriesPoint
from app.services.metrics import get_metrics_summary, get_metrics_timeseries

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummary)
async def metrics_summary(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, ge=1, le=720),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return await get_metrics_summary(db, project.id, since)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
async def metrics_timeseries(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    bucket_type: str = Query("hour", pattern="^(hour|day)$"),
    days: int = Query(7, ge=1, le=90),
    group_by: str | None = Query(None),
):
    return await get_metrics_timeseries(
        db, project.id, bucket_type=bucket_type, days=days, group_by_model=group_by == "model"
    )
