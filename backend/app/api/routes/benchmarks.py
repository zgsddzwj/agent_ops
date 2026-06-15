import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.database import get_db
from app.models import ModelBenchmark, ModelBenchmarkResult, Project
from app.schemas import BenchmarkCreate, BenchmarkResponse
from app.services.ingest import percentile
from app.services.task_queue import enqueue_task

router = APIRouter(prefix="/v1/benchmarks", tags=["benchmarks"])


@router.post("", response_model=BenchmarkResponse)
async def create_benchmark(
    body: BenchmarkCreate,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    benchmark = ModelBenchmark(
        project_id=project.id,
        dataset_id=body.dataset_id,
        models_json=body.models,
        repeat_count=body.repeat_count,
        status="pending",
    )
    db.add(benchmark)
    await db.flush()

    await enqueue_task(
        "run_benchmark_task",
        {
            "benchmark_id": str(benchmark.id),
            "project_id": str(project.id),
            "items": body.items,
        },
    )
    return benchmark


@router.get("", response_model=list[BenchmarkResponse])
async def list_benchmarks(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(ModelBenchmark)
        .where(ModelBenchmark.project_id == project.id)
        .order_by(ModelBenchmark.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(
    benchmark_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelBenchmark).where(
            ModelBenchmark.id == benchmark_id, ModelBenchmark.project_id == project.id
        )
    )
    benchmark = result.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark


@router.get("/{benchmark_id}/compare")
async def compare_benchmark(
    benchmark_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ModelBenchmark).where(
            ModelBenchmark.id == benchmark_id, ModelBenchmark.project_id == project.id
        )
    )
    benchmark = result.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    if benchmark.summary_json:
        return benchmark.summary_json

    results_result = await db.execute(
        select(ModelBenchmarkResult).where(ModelBenchmarkResult.benchmark_id == benchmark_id)
    )
    results = results_result.scalars().all()

    by_model: dict[str, list] = {}
    for r in results:
        key = f"{r.provider}:{r.model}"
        by_model.setdefault(key, []).append(r)

    comparison = []
    for key, model_results in by_model.items():
        provider, model = key.split(":", 1)
        ttfts = [r.ttft_ms for r in model_results if r.ttft_ms is not None]
        e2es = [r.e2e_latency_ms for r in model_results if r.e2e_latency_ms is not None]
        costs = [r.cost_usd for r in model_results if r.cost_usd is not None]
        scores = [r.eval_score for r in model_results if r.eval_score is not None]
        errors = sum(1 for r in model_results if r.error)

        comparison.append(
            {
                "provider": provider,
                "model": model,
                "ttft_p50": percentile(ttfts, 50),
                "ttft_p95": percentile(ttfts, 95),
                "e2e_p50": percentile(e2es, 50),
                "e2e_p95": percentile(e2es, 95),
                "avg_cost_usd": sum(costs) / len(costs) if costs else None,
                "avg_eval_score": sum(scores) / len(scores) if scores else None,
                "error_rate": errors / len(model_results) if model_results else 0,
                "sample_count": len(model_results),
                "cases": [
                    {
                        "case_index": r.case_index,
                        "repeat_index": r.repeat_index,
                        "ttft_ms": r.ttft_ms,
                        "e2e_latency_ms": r.e2e_latency_ms,
                        "cost_usd": r.cost_usd,
                        "eval_score": r.eval_score,
                        "output_text": r.output_text,
                        "error": r.error,
                    }
                    for r in model_results
                ],
            }
        )

    return {"benchmark_id": str(benchmark_id), "models": comparison, "status": benchmark.status}
