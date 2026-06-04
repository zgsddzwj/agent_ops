import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MetricAggregate, Run
from app.schemas import MetricsSummary, TimeseriesPoint
from app.services.ingest import percentile


async def get_metrics_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
    since: datetime | None = None,
) -> MetricsSummary:
    query = select(Run).where(Run.project_id == project_id)
    if since:
        query = query.where(Run.created_at >= since)
    result = await db.execute(query)
    runs = result.scalars().all()

    if not runs:
        return MetricsSummary(
            total_runs=0,
            error_rate=0.0,
            total_cost_usd=0.0,
            total_tokens=0,
            avg_latency_ms=None,
            p50_latency_ms=None,
            p95_latency_ms=None,
            p50_ttft_ms=None,
            p95_ttft_ms=None,
        )

    latencies = [r.latency_ms for r in runs if r.latency_ms is not None]
    ttfts = [r.ttft_ms for r in runs if r.ttft_ms is not None]
    errors = sum(1 for r in runs if r.status == "error")

    return MetricsSummary(
        total_runs=len(runs),
        error_rate=errors / len(runs) if runs else 0.0,
        total_cost_usd=sum(r.cost_usd or 0 for r in runs),
        total_tokens=sum(r.total_tokens or 0 for r in runs),
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else None,
        p50_latency_ms=percentile(latencies, 50),
        p95_latency_ms=percentile(latencies, 95),
        p50_ttft_ms=percentile(ttfts, 50),
        p95_ttft_ms=percentile(ttfts, 95),
    )


async def get_metrics_timeseries(
    db: AsyncSession,
    project_id: uuid.UUID,
    bucket_type: str = "hour",
    days: int = 7,
    group_by_model: bool = False,
) -> list[TimeseriesPoint]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(MetricAggregate).where(
        MetricAggregate.project_id == project_id,
        MetricAggregate.bucket_start >= since,
        MetricAggregate.bucket_type == bucket_type,
    )
    if not group_by_model:
        query = query.where(
            MetricAggregate.model_provider.is_(None),
            MetricAggregate.model_name.is_(None),
        )
    query = query.order_by(MetricAggregate.bucket_start)
    result = await db.execute(query)
    aggregates = result.scalars().all()

    if aggregates:
        return [
            TimeseriesPoint(
                bucket=a.bucket_start,
                run_count=a.run_count,
                total_cost_usd=a.total_cost_usd,
                avg_latency_ms=a.avg_latency_ms,
                p95_latency_ms=a.p95_latency_ms,
                model_provider=a.model_provider,
                model_name=a.model_name,
            )
            for a in aggregates
        ]

    # Fallback: compute from runs if no aggregates yet
    runs_result = await db.execute(
        select(Run).where(Run.project_id == project_id, Run.created_at >= since)
    )
    runs = runs_result.scalars().all()
    buckets: dict[datetime, list[Run]] = {}
    for run in runs:
        if bucket_type == "day":
            bucket = run.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            bucket = run.created_at.replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(bucket, []).append(run)

    points = []
    for bucket, bucket_runs in sorted(buckets.items()):
        latencies = [r.latency_ms for r in bucket_runs if r.latency_ms is not None]
        points.append(
            TimeseriesPoint(
                bucket=bucket,
                run_count=len(bucket_runs),
                total_cost_usd=sum(r.cost_usd or 0 for r in bucket_runs),
                avg_latency_ms=sum(latencies) / len(latencies) if latencies else None,
                p95_latency_ms=percentile(latencies, 95),
            )
        )
    return points
