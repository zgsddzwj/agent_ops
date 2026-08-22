"""FastAPI dependency injection for API key authentication."""

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_api_key, verify_api_key
from app.models import Project


async def get_current_project(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Authenticate request via X-API-Key header and return the associated project."""
    key_hash = hash_api_key(x_api_key)
    result = await db.execute(select(Project).where(Project.api_key_hash == key_hash))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    # Verify using constant-time comparison to prevent timing attacks
    if not verify_api_key(x_api_key, project.api_key_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return project


async def get_optional_project(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Project | None:
    """Optionally authenticate request. Returns None if no API key provided."""
    if not x_api_key:
        return None
    key_hash = hash_api_key(x_api_key)
    result = await db.execute(select(Project).where(Project.api_key_hash == key_hash))
    project = result.scalar_one_or_none()
    if project and not verify_api_key(x_api_key, project.api_key_hash):
        return None
    return project
