import uuid
from datetime import datetime, timedelta, timezone

from functools import lru_cache
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
    """Calculate comprehensive metrics summary for a project over the specified time period.
    
    This function aggregates run data to provide key performance indicators including
    error rates, costs, latency statistics, and token usage. For better performance,
    it's recommended to use pre-aggregated MetricAggregate data when available.
    
    Args:
        db: Async database session
        project_id: UUID of the project to analyze
        since: Optional timestamp filter - only include runs after this time
        
    Returns:
        MetricsSummary containing aggregated metrics across all matching runs
        
    Performance Note:
        This function loads all runs into memory. For large datasets, consider
        implementing pagination or using the get_metrics_timeseries function
        which queries pre-aggregated data.
    """
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

    # Use single list comprehensions to reduce memory allocation
    latencies = []
    ttfts = []
    errors = 0
    total_cost = 0.0
    total_tokens = 0
    
    for run in runs:
        if run.latency_ms is not None:
            latencies.append(run.latency_ms)
        if run.ttft_ms is not None:
            ttfts.append(run.ttft_ms)
        if run.status == "error":
            errors += 1
        total_cost += run.cost_usd or 0
        total_tokens += run.total_tokens or 0

    total_runs = len(runs)
    
    # Avoid duplicate len() calls
    latency_count = len(latencies) if latencies else 0
    ttft_count = len(ttfts) if ttfts else 0

    return MetricsSummary(
        total_runs=total_runs,
        error_rate=errors / total_runs,
        total_cost_usd=total_cost,
        total_tokens=total_tokens,
        avg_latency_ms=sum(latencies) / latency_count if latency_count > 0 else None,
        p50_latency_ms=percentile(latencies, 50) if latencies else None,
        p95_latency_ms=percentile(latencies, 95) if latencies else None,
        p50_ttft_ms=percentile(ttfts, 50) if ttfts else None,
        p95_ttft_ms=percentile(ttfts, 95) if ttfts else None,
    )


async def get_metrics_timeseries(
    db: AsyncSession,
    project_id: uuid.UUID,
    bucket_type: str = "hour",
    days: int = 7,
    group_by_model: bool = False,
) -> list[TimeseriesPoint]:
    """Generate time-series metrics for visualization and trend analysis.
    
    Retrieves aggregated metrics over time buckets (hourly/daily) to show
    performance trends, cost patterns, and usage statistics. First attempts
    to use pre-aggregated MetricAggregate data for better performance, with
    fallback to on-the-fly computation from raw run data.
    
    Args:
        db: Async database session
        project_id: UUID of the project to analyze
        bucket_type: Time bucket size - either "hour" or "day"
        days: Number of days to look back for data
        group_by_model: Whether to separate metrics by model provider/name
        
    Returns:
        List of TimeseriesPoint objects sorted by timestamp
        
    Database Optimization:
        Uses pre-aggregated MetricAggregate table when available to avoid
        expensive real-time aggregations on the Run table.
    """
    if bucket_type not in ("hour", "day"):
        raise ValueError(f"Invalid bucket_type '{bucket_type}'. Must be 'hour' or 'day'.")
    
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # First, try to get pre-aggregated data for performance
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
        # Sort by bucket time to ensure chronological order
        sorted_aggregates = sorted(aggregates, key=lambda a: a.bucket_start)
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
            for a in sorted_aggregates
        ]

    # Fallback: compute aggregates from raw run data
    # Note: This is expensive for large datasets. Consider running background
    # aggregation jobs to populate MetricAggregate table.
    runs_result = await db.execute(
        select(Run).where(Run.project_id == project_id, Run.created_at >= since)
    )
    runs = runs_result.scalars().all()
    
    if not runs:
        return []
    
    # Group runs by time bucket using more efficient dictionary operations
    buckets: dict[datetime, dict] = {}
    
    for run in runs:
        # Normalize timestamp to bucket start
        if bucket_type == "day":
            bucket = run.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # hour
            bucket = run.created_at.replace(minute=0, second=0, microsecond=0)
        
        if bucket not in buckets:
            buckets[bucket] = {
                "runs": [],
                "total_cost": 0.0,
                "latencies": [],
            }
        
        buckets[bucket]["runs"].append(run)
        buckets[bucket]["total_cost"] += run.cost_usd or 0
        
        if run.latency_ms is not None:
            buckets[bucket]["latencies"].append(run.latency_ms)

    # Build result points with proper error handling
    points = []
    for bucket_time in sorted(buckets.keys()):
        bucket_data = buckets[bucket_time]
        latencies = bucket_data["latencies"]
        
        avg_latency = None
        p95_latency = None
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = percentile(latencies, 95)
        
        point = TimeseriesPoint(
            bucket=bucket_time,
            run_count=len(bucket_data["runs"]),
            total_cost_usd=bucket_data["total_cost"],
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            # No model-specific data in fallback mode
            model_provider=None,
            model_name=None,
        )
        
        points.append(point)
    
    return points
