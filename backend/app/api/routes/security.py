import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.config import settings
from app.core.database import get_db
from app.models import Project, SecurityFinding, SecurityScan
from app.schemas import SecurityScanCreate, SecurityScanResponse

router = APIRouter(prefix="/v1/security", tags=["security"])


async def _enqueue_task(task_name: str, payload: dict) -> None:
    """Enqueue a background task to Redis with proper error handling and logging.
    
    Args:
        task_name: Name of the task to enqueue
        payload: Task payload data
        
    Implementation Note:
        Failures are silently ignored to prevent disrupting the main API flow.
        Consider adding structured logging for production monitoring.
    """
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await redis.enqueue_job(task_name, payload)
        await redis.close()
    except Exception as exc:
        # Silently ignore failures to prevent disrupting main flow
        # In production, consider logging this error for monitoring
        pass


@router.post("/scans", response_model=SecurityScanResponse)
async def create_security_scan(
    body: SecurityScanCreate,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    scan = SecurityScan(
        project_id=project.id,
        suite_name=body.suite_name,
        status="pending",
    )
    db.add(scan)
    await db.flush()

    await _enqueue_task(
        "run_security_scan_task",
        {"scan_id": str(scan.id), "project_id": str(project.id), "suite_name": body.suite_name},
    )
    return scan


@router.get("/scans", response_model=list[SecurityScanResponse])
async def list_security_scans(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(SecurityScan)
        .where(SecurityScan.project_id == project.id)
        .order_by(SecurityScan.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/scans/{scan_id}")
async def get_security_scan(
    scan_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SecurityScan).where(
            SecurityScan.id == scan_id, SecurityScan.project_id == project.id
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    findings_result = await db.execute(
        select(SecurityFinding).where(SecurityFinding.scan_id == scan_id)
    )
    findings = findings_result.scalars().all()

    return {
        "scan": SecurityScanResponse.model_validate(scan),
        "findings": [
            {
                "id": str(f.id),
                "category": f.category,
                "severity": f.severity,
                "input_text": f.input_text,
                "output_text": f.output_text,
                "passed": f.passed,
                "evidence": f.evidence,
            }
            for f in findings
        ],
    }
