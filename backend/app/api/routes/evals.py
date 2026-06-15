import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.database import get_db
from app.models import EvalResult, EvalRun, Project
from app.schemas import EvalResultResponse, EvalRunCreate, EvalRunResponse
from app.services.task_queue import enqueue_task

router = APIRouter(prefix="/v1/eval", tags=["eval"])


@router.post("/runs", response_model=EvalRunResponse)
async def create_eval_run(
    body: EvalRunCreate,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    eval_run = EvalRun(
        project_id=project.id,
        dataset_id=body.dataset_id,
        suite_name=body.suite_name,
        baseline_id=body.baseline_id,
        status="pending",
    )
    db.add(eval_run)
    await db.flush()

    await enqueue_task(
        "run_eval_task",
        {
            "eval_run_id": str(eval_run.id),
            "project_id": str(project.id),
            "items": body.items,
        },
    )
    return eval_run


@router.get("/runs", response_model=list[EvalRunResponse])
async def list_eval_runs(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.project_id == project.id)
        .order_by(EvalRun.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=EvalRunResponse)
async def get_eval_run(
    run_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EvalRun).where(EvalRun.id == run_id, EvalRun.project_id == project.id)
    )
    eval_run = result.scalar_one_or_none()
    if not eval_run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return eval_run


@router.get("/runs/{run_id}/results", response_model=list[EvalResultResponse])
async def get_eval_results(
    run_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    run_result = await db.execute(
        select(EvalRun).where(EvalRun.id == run_id, EvalRun.project_id == project.id)
    )
    if not run_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Eval run not found")

    result = await db.execute(select(EvalResult).where(EvalResult.eval_run_id == run_id))
    return result.scalars().all()
