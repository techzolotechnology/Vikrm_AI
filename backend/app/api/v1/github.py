"""
GitHub API router.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.project import GitHubIntegration
from app.models.user import User
from app.services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["GitHub"])


class ConnectGitHubRequest(BaseModel):
    access_token: str
    username: Optional[str] = None


class CreatePRRequest(BaseModel):
    repo: str
    title: str
    head: str
    base: Optional[str] = "main"
    body: Optional[str] = ""


@router.get("/status")
async def get_github_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(GitHubIntegration).where(GitHubIntegration.user_id == user.id)
    res = await db.execute(stmt)
    gh = res.scalar_one_or_none()
    return {"connected": gh is not None, "username": gh.username if gh else None}


@router.post("/connect")
async def connect_github(
    req: ConnectGitHubRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(GitHubIntegration).where(GitHubIntegration.user_id == user.id)
    res = await db.execute(stmt)
    gh = res.scalar_one_or_none()
    if gh:
        gh.access_token = req.access_token
        if req.username:
            gh.username = req.username
    else:
        gh = GitHubIntegration(user_id=user.id, access_token=req.access_token, username=req.username or "dev-user")
        db.add(gh)
    await db.commit()
    return {"message": "GitHub connected successfully", "username": gh.username}


@router.get("/repos")
async def list_user_repos(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(GitHubIntegration).where(GitHubIntegration.user_id == user.id)
    res = await db.execute(stmt)
    gh = res.scalar_one_or_none()
    token = gh.access_token if gh else "dummy_token"
    repos = await GitHubService.get_user_repos(token)
    return {"repos": repos}


@router.post("/pull-requests")
async def create_pr(
    req: CreatePRRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(GitHubIntegration).where(GitHubIntegration.user_id == user.id)
    res = await db.execute(stmt)
    gh = res.scalar_one_or_none()
    token = gh.access_token if gh else "dummy_token"
    pr = await GitHubService.create_pull_request(
        access_token=token, repo=req.repo, title=req.title, head=req.head, base=req.base, body=req.body
    )
    return pr
