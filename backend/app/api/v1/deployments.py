"""
Deployments API router.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.project import Deployment, Project
from app.models.user import User
from app.services.deployment_service import DeploymentService

router = APIRouter(prefix="/deployments", tags=["Deployments"])


class TriggerDeploymentRequest(BaseModel):
    project_id: int
    target: str  # vercel, netlify, railway, render, docker, kubernetes


@router.post("")
async def trigger_deployment(
    req: TriggerDeploymentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == req.project_id, Project.user_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await DeploymentService.trigger_deployment(req.target, project.title)

    dep = Deployment(
        project_id=project.id,
        target=req.target.upper(),
        status=result["status"],
        url=result["url"],
        logs=result["logs"],
    )
    db.add(dep)
    await db.commit()
    await db.refresh(dep)

    return {
        "id": dep.id,
        "project_id": dep.project_id,
        "target": dep.target,
        "status": dep.status,
        "url": dep.url,
        "logs": dep.logs,
    }
