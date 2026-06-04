import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.database import get_db
from app.models import AlertEvent, AlertRule, Project
from app.schemas import AlertEventResponse, AlertRuleCreate, AlertRuleResponse

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    body: AlertRuleCreate,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    rule = AlertRule(
        project_id=project.id,
        name=body.name,
        rule_type=body.rule_type,
        threshold=body.threshold,
        window_minutes=body.window_minutes,
        webhook_url=body.webhook_url,
    )
    db.add(rule)
    await db.flush()
    return rule


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(AlertRule.project_id == project.id)
    )
    return result.scalars().all()


@router.get("/events", response_model=list[AlertEventResponse])
async def list_alert_events(
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(AlertEvent)
        .where(AlertEvent.project_id == project.id)
        .order_by(AlertEvent.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.patch("/events/{event_id}/acknowledge")
async def acknowledge_event(
    event_id: uuid.UUID,
    project: Project = Depends(get_current_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertEvent).where(
            AlertEvent.id == event_id, AlertEvent.project_id == project.id
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.acknowledged = True
    await db.flush()
    return {"status": "ok"}
