import uuid

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project
from app.core.database import get_db
from app.core.security import generate_api_key
from app.models import Project, ProjectConfig
from app.schemas import (
    ProjectConfigUpdate,
    ProjectCreate,
    ProjectCreateResponse,
    ProjectResponse,
)

router = APIRouter(prefix="/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectCreateResponse)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Project).where(Project.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project name already exists")

    api_key, key_hash, prefix = generate_api_key()
    config_json = None
    if body.config_yaml:
        try:
            config_json = yaml.safe_load(body.config_yaml)
        except yaml.YAMLError:
            config_json = {"raw": body.config_yaml}

    project = Project(
        name=body.name,
        root_path=body.root_path,
        entrypoint=body.entrypoint,
        api_key_hash=key_hash,
        api_key_prefix=prefix,
        config_json=config_json,
    )
    db.add(project)
    await db.flush()

    if body.config_yaml:
        db.add(ProjectConfig(project_id=project.id, config_yaml=body.config_yaml))

    return ProjectCreateResponse(
        id=project.id,
        name=project.name,
        root_path=project.root_path,
        entrypoint=project.entrypoint,
        api_key_prefix=project.api_key_prefix,
        created_at=project.created_at,
        api_key=api_key,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}/config")
async def update_project_config(
    project_id: uuid.UUID,
    body: ProjectConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        project.config_json = yaml.safe_load(body.config_yaml)
    except yaml.YAMLError:
        project.config_json = {"raw": body.config_yaml}

    db.add(ProjectConfig(project_id=project.id, config_yaml=body.config_yaml))
    return {"status": "ok"}


@router.get("/me/info", response_model=ProjectResponse)
async def get_my_project(project: Project = Depends(get_current_project)):
    return project
