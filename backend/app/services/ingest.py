import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModelPricing, Run, Span


DEFAULT_PRICING = [
    ("openai", "gpt-4o", 2.50, 10.00),
    ("openai", "gpt-4o-mini", 0.15, 0.60),
    ("openai", "gpt-4-turbo", 10.00, 30.00),
    ("qwen", "qwen-plus", 0.40, 1.20),
    ("qwen", "qwen-turbo", 0.05, 0.15),
    ("qwen", "qwen-max", 1.60, 6.40),
    ("deepseek", "deepseek-chat", 0.14, 0.28),
    ("deepseek", "deepseek-reasoner", 0.55, 2.19),
    ("anthropic", "claude-sonnet-4-20250514", 3.00, 15.00),
    ("anthropic", "claude-3-5-sonnet-20241022", 3.00, 15.00),
    ("zhipu", "glm-4", 0.70, 0.70),
]


async def seed_model_pricing(db: AsyncSession) -> None:
    for provider, model, inp, out in DEFAULT_PRICING:
        existing = await db.execute(
            select(ModelPricing).where(
                ModelPricing.provider == provider, ModelPricing.model == model
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                ModelPricing(
                    provider=provider,
                    model=model,
                    input_price_per_1k=inp,
                    output_price_per_1k=out,
                )
            )


async def calculate_span_cost(
    db: AsyncSession,
    provider: str | None,
    model: str | None,
    tokens_in: int | None,
    tokens_out: int | None,
) -> float | None:
    """Calculate the cost of a span based on model pricing.
    
    Looks up pricing information from the database first, then falls back to
    looking up by provider and model combination. Returns None if pricing
    information is not available.
    
    Args:
        db: Async database session
        provider: LLM provider name (e.g., "openai", "qwen")
        model: Model name (e.g., "gpt-4o", "qwen-plus")
        tokens_in: Number of input/prompt tokens
        tokens_out: Number of output/completion tokens
        
    Returns:
        Calculated cost in USD, or None if pricing not found
    """
    if not model:
        return None
    
    tokens_in = tokens_in or 0
    tokens_out = tokens_out or 0
    
    # Try lookup by model name only
    result = await db.execute(
        select(ModelPricing).where(ModelPricing.model == model)
    )
    pricing = result.scalar_one_or_none()
    
    # If not found and provider specified, try provider+model combination
    if not pricing and provider:
        result = await db.execute(
            select(ModelPricing).where(
                ModelPricing.provider == provider, ModelPricing.model == model
            )
        )
        pricing = result.scalar_one_or_none()
    
    if not pricing:
        return None
    
    # Calculate cost: (input_tokens * input_price) + (output_tokens * output_price)
    input_cost = (tokens_in / 1000) * pricing.input_price_per_1k
    output_cost = (tokens_out / 1000) * pricing.output_price_per_1k
    
    return input_cost + output_cost


async def ingest_trace(
    db: AsyncSession,
    project_id: uuid.UUID,
    run_data: dict | None,
    spans_data: list[dict],
) -> tuple[Run, list[Span]]:
    run_id = run_data.get("id") if run_data else None
    if run_id:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
    else:
        run = None

    if run is None:
        run = Run(
            id=run_id or uuid.uuid4(),
            project_id=project_id,
            name=run_data.get("name") if run_data else None,
            status=run_data.get("status", "running") if run_data else "running",
            model_provider=run_data.get("model_provider") if run_data else None,
            model_name=run_data.get("model_name") if run_data else None,
            metadata_json=run_data.get("metadata") if run_data else None,
        )
        db.add(run)
        await db.flush()
    elif run_data:
        for field in ("status", "model_provider", "model_name"):
            if run_data.get(field) is not None:
                setattr(run, field, run_data[field])
        if run_data.get("metadata"):
            run.metadata_json = run_data["metadata"]

    spans: list[Span] = []
    total_tokens = 0
    total_cost = 0.0
    max_ttft = None

    for s in spans_data:
        cost = s.get("cost_usd")
        if cost is None:
            cost = await calculate_span_cost(
                db, s.get("provider"), s.get("model"), s.get("tokens_in"), s.get("tokens_out")
            )
        span = Span(
            id=s.get("id") or uuid.uuid4(),
            run_id=run.id,
            parent_id=s.get("parent_id"),
            span_type=s["span_type"],
            name=s.get("name"),
            input_json=s.get("input"),
            output_json=s.get("output"),
            model=s.get("model"),
            provider=s.get("provider"),
            tokens_in=s.get("tokens_in"),
            tokens_out=s.get("tokens_out"),
            latency_ms=s.get("latency_ms"),
            ttft_ms=s.get("ttft_ms"),
            tokens_per_sec=s.get("tokens_per_sec"),
            cost_usd=cost,
            status=s.get("status", "success"),
            error=s.get("error"),
            started_at=s.get("started_at"),
            ended_at=s.get("ended_at"),
        )
        db.add(span)
        spans.append(span)
        total_tokens += (s.get("tokens_in") or 0) + (s.get("tokens_out") or 0)
        if cost:
            total_cost += cost
        if s.get("ttft_ms") is not None:
            max_ttft = s["ttft_ms"] if max_ttft is None else min(max_ttft, s["ttft_ms"])

    if run_data:
        if run_data.get("latency_ms") is not None:
            run.latency_ms = run_data["latency_ms"]
        if run_data.get("ttft_ms") is not None:
            run.ttft_ms = run_data["ttft_ms"]
        elif max_ttft is not None:
            run.ttft_ms = max_ttft
        if run_data.get("total_tokens") is not None:
            run.total_tokens = run_data["total_tokens"]
        else:
            run.total_tokens = total_tokens
        if run_data.get("cost_usd") is not None:
            run.cost_usd = run_data["cost_usd"]
        else:
            run.cost_usd = total_cost or None
        if run_data.get("status"):
            run.status = run_data["status"]
            if run_data["status"] in ("success", "error"):
                run.finished_at = datetime.now(timezone.utc)
        if run_data.get("error"):
            run.error = run_data["error"]

    await db.flush()
    return run, spans


def percentile(values: list[float], p: float) -> float | None:
    """Calculate the p-th percentile of a list of values.
    
    Uses linear interpolation between the two closest ranks when the percentile
    position is not an integer. This follows the R-7 method commonly used in 
    statistical software.
    
    Args:
        values: List of float values to calculate percentile from
        p: Percentile to calculate (0-100)
        
    Returns:
        The p-th percentile value, or None if list is empty
        
    Examples:
        >>> percentile([1, 2, 3, 4, 5], 50)  # 50th percentile (median)
        3.0
        >>> percentile([1, 2, 3, 4], 75)       # 75th percentile
        3.25
    """
    if not values:
        return None
    
    if len(values) == 1:
        return values[0]
    
    sorted_vals = sorted(values)
    # Calculate position using R-7 method (linear interpolation)
    n = len(sorted_vals)
    pos = (p / 100) * (n - 1)
    
    if pos.is_integer():
        # Exact position
        return sorted_vals[int(pos)]
    else:
        # Linear interpolation between two closest values
        lower_idx = int(pos)
        upper_idx = lower_idx + 1
        weight = pos - lower_idx
        
        lower_val = sorted_vals[lower_idx]
        upper_val = sorted_vals[min(upper_idx, n - 1)]
        
        return lower_val + weight * (upper_val - lower_val)
