import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.database import get_db
from app.models import Project, Run, Span
from app.schemas import RunCreate, RunResponse, RunUpdate, SpanIngest, SpanResponse, TraceIngestRequest
from app.services.ingest import ingest_trace

router = APIRouter(prefix="/v1", tags=["traces"])


@router.post("/traces/ingest")
async def ingest_traces(
    body: TraceIngestRequest,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    run_data = body.run.model_dump() if body.run else None
    spans_data = [s.model_dump() for s in body.spans]
    for s in spans_data:
        if "input" in s:
            s["input_json"] = s.pop("input")
        if "output" in s:
            s["output_json"] = s.pop("output")
    # Normalize keys for ingest service
    normalized_spans = []
    for s in spans_data:
        normalized_spans.append(
            {
                "id": s.get("id"),
                "run_id": s["run_id"],
                "parent_id": s.get("parent_id"),
                "span_type": s["span_type"],
                "name": s.get("name"),
                "input": s.get("input_json") or s.get("input"),
                "output": s.get("output_json") or s.get("output"),
                "model": s.get("model"),
                "provider": s.get("provider"),
                "tokens_in": s.get("tokens_in"),
                "tokens_out": s.get("tokens_out"),
                "latency_ms": s.get("latency_ms"),
                "ttft_ms": s.get("ttft_ms"),
                "tokens_per_sec": s.get("tokens_per_sec"),
                "cost_usd": s.get("cost_usd"),
                "status": s.get("status", "success"),
                "error": s.get("error"),
                "started_at": s.get("started_at"),
                "ended_at": s.get("ended_at"),
            }
        )

    run, spans = await ingest_trace(db, project.id, run_data, normalized_spans)
    return {"run_id": str(run.id), "spans_ingested": len(spans)}


@router.post("/runs", response_model=RunResponse)
async def create_run(
    body: RunCreate,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    run = Run(
        id=body.id or uuid.uuid4(),
        project_id=project.id,
        name=body.name,
        status=body.status,
        model_provider=body.model_provider,
        model_name=body.model_name,
        metadata_json=body.metadata,
    )
    db.add(run)
    await db.flush()
    return run


@router.patch("/runs/{run_id}", response_model=RunResponse)
async def update_run(
    run_id: uuid.UUID,
    body: RunUpdate,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.project_id == project.id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(run, field, value)
    if body.status in ("success", "error"):
        run.finished_at = datetime.now(timezone.utc)
    await db.flush()
    return run


@router.get("/runs", response_model=list[RunResponse])
async def list_runs(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Run).where(Run.project_id == project.id)
    if status:
        query = query.where(Run.status == status)
    query = query.order_by(Run.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.project_id == project.id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/spans", response_model=list[SpanResponse])
async def get_run_spans(
    run_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    run_result = await db.execute(
        select(Run).where(Run.id == run_id, Run.project_id == project.id)
    )
    if not run_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Run not found")

    result = await db.execute(select(Span).where(Span.run_id == run_id).order_by(Span.started_at))
    return result.scalars().all()
