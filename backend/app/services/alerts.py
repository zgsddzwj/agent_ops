import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertEvent, AlertRule, MetricAggregate, Run, SecurityScan


async def aggregate_metrics(db: AsyncSession, project_id: uuid.UUID | None = None) -> int:
    """Hourly aggregation of run metrics."""
    now = datetime.now(timezone.utc)
    bucket_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    bucket_end = bucket_start + timedelta(hours=1)

    query = select(Run).where(Run.created_at >= bucket_start, Run.created_at < bucket_end)
    if project_id:
        query = query.where(Run.project_id == project_id)
    result = await db.execute(query)
    runs = result.scalars().all()

    if not runs:
        return 0

    by_project: dict[uuid.UUID, list[Run]] = {}
    for run in runs:
        by_project.setdefault(run.project_id, []).append(run)

    count = 0
    for pid, project_runs in by_project.items():
        latencies = [r.latency_ms for r in project_runs if r.latency_ms is not None]
        ttfts = [r.ttft_ms for r in project_runs if r.ttft_ms is not None]
        errors = sum(1 for r in project_runs if r.status == "error")

        agg = MetricAggregate(
            project_id=pid,
            bucket_start=bucket_start,
            bucket_type="hour",
            run_count=len(project_runs),
            error_count=errors,
            total_cost_usd=sum(r.cost_usd or 0 for r in project_runs),
            total_tokens=sum(r.total_tokens or 0 for r in project_runs),
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else None,
            p50_latency_ms=_percentile(latencies, 50),
            p95_latency_ms=_percentile(latencies, 95),
            p50_ttft_ms=_percentile(ttfts, 50),
            p95_ttft_ms=_percentile(ttfts, 95),
        )
        db.add(agg)
        count += 1

        # Per-model aggregates
        by_model: dict[tuple[str | None, str | None], list[Run]] = {}
        for run in project_runs:
            key = (run.model_provider, run.model_name)
            by_model.setdefault(key, []).append(run)

        for (provider, model), model_runs in by_model.items():
            if not provider and not model:
                continue
            m_latencies = [r.latency_ms for r in model_runs if r.latency_ms is not None]
            m_ttfts = [r.ttft_ms for r in model_runs if r.ttft_ms is not None]
            db.add(
                MetricAggregate(
                    project_id=pid,
                    bucket_start=bucket_start,
                    bucket_type="hour",
                    model_provider=provider,
                    model_name=model,
                    run_count=len(model_runs),
                    error_count=sum(1 for r in model_runs if r.status == "error"),
                    total_cost_usd=sum(r.cost_usd or 0 for r in model_runs),
                    total_tokens=sum(r.total_tokens or 0 for r in model_runs),
                    avg_latency_ms=sum(m_latencies) / len(m_latencies) if m_latencies else None,
                    p50_latency_ms=_percentile(m_latencies, 50),
                    p95_latency_ms=_percentile(m_latencies, 95),
                    p50_ttft_ms=_percentile(m_ttfts, 50),
                    p95_ttft_ms=_percentile(m_ttfts, 95),
                )
            )
            count += 1

    await db.flush()
    return count


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    idx = min(int(len(sorted_vals) * p / 100), len(sorted_vals) - 1)
    return sorted_vals[idx]


async def evaluate_alert_rules(db: AsyncSession) -> list[AlertEvent]:
    """Check enabled alert rules and fire events."""
    result = await db.execute(select(AlertRule).where(AlertRule.enabled == True))  # noqa: E712
    rules = result.scalars().all()
    events: list[AlertEvent] = []

    for rule in rules:
        since = datetime.now(timezone.utc) - timedelta(minutes=rule.window_minutes)
        triggered = False
        value = None
        message = ""

        if rule.rule_type == "cost_threshold":
            runs_result = await db.execute(
                select(func.sum(Run.cost_usd)).where(
                    Run.project_id == rule.project_id, Run.created_at >= since
                )
            )
            value = runs_result.scalar() or 0.0
            if value > rule.threshold:
                triggered = True
                message = f"Cost ${value:.4f} exceeded threshold ${rule.threshold:.4f}"

        elif rule.rule_type == "latency_p95":
            runs_result = await db.execute(
                select(Run.latency_ms).where(
                    Run.project_id == rule.project_id,
                    Run.created_at >= since,
                    Run.latency_ms.isnot(None),
                )
            )
            latencies = [r for r in runs_result.scalars().all()]
            value = _percentile(latencies, 95) or 0.0
            if value > rule.threshold:
                triggered = True
                message = f"P95 latency {value:.0f}ms exceeded threshold {rule.threshold:.0f}ms"

        elif rule.rule_type == "error_rate":
            runs_result = await db.execute(
                select(Run).where(Run.project_id == rule.project_id, Run.created_at >= since)
            )
            runs = runs_result.scalars().all()
            if runs:
                value = sum(1 for r in runs if r.status == "error") / len(runs)
                if value > rule.threshold:
                    triggered = True
                    message = f"Error rate {value:.1%} exceeded threshold {rule.threshold:.1%}"

        elif rule.rule_type == "security_pass_rate":
            scans_result = await db.execute(
                select(SecurityScan).where(
                    SecurityScan.project_id == rule.project_id,
                    SecurityScan.created_at >= since,
                    SecurityScan.pass_rate.isnot(None),
                )
            )
            scans = scans_result.scalars().all()
            if scans:
                value = sum(s.pass_rate or 0 for s in scans) / len(scans)
                if value < rule.threshold:
                    triggered = True
                    message = f"Security pass rate {value:.1%} below threshold {rule.threshold:.1%}"

        if triggered:
            event = AlertEvent(
                rule_id=rule.id,
                project_id=rule.project_id,
                message=message,
                value=value,
            )
            db.add(event)
            events.append(event)

            if rule.webhook_url:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(
                            rule.webhook_url,
                            json={"message": message, "value": value, "rule": rule.name},
                        )
                except Exception:
                    pass

    await db.flush()
    return events
