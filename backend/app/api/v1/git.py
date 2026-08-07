"""
Git Integration API — Professional AI IDE.

Phase 1 Status: Marked explicitly as not_yet_implemented pending Phase 8 git_workspace_service.py integration.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/git", tags=["Git"])


class GitCommitRequest(BaseModel):
    project_id: int
    message: str
    branch: str = "main"


class GitCheckoutRequest(BaseModel):
    project_id: int
    branch: str


class GitMergeRequest(BaseModel):
    project_id: int
    source_branch: str
    target_branch: str = "main"


@router.get("/status/{project_id}")
async def git_status(project_id: int, _user: User = Depends(get_current_user)):
    return {
        "status": "not_yet_implemented",
        "branch": "main",
        "branches": ["main"],
        "commits": 0,
        "staged": [],
        "modified": [],
        "clean": True,
        "message": "Phase 1: Real git status pending Phase 8 git_workspace_service.py integration.",
        "is_simulated": True,
    }


@router.post("/commit")
async def git_commit(req: GitCommitRequest, _user: User = Depends(get_current_user)):
    return {
        "status": "not_yet_implemented",
        "hash": None,
        "message": f"Phase 1: Git commit not_yet_implemented. Real git commit pending Phase 8 git_workspace_service.py. Requested message: {req.message}",
        "branch": req.branch,
        "is_simulated": True,
    }


@router.get("/history/{project_id}")
async def git_history(project_id: int, _user: User = Depends(get_current_user)):
    return {
        "status": "not_yet_implemented",
        "commits": [],
        "branch": "main",
        "message": "Phase 1: Real git log history pending Phase 8 git_workspace_service.py.",
        "is_simulated": True,
    }


@router.get("/branches/{project_id}")
async def git_branches(project_id: int, _user: User = Depends(get_current_user)):
    return {
        "status": "not_yet_implemented",
        "branches": ["main"],
        "current": "main",
        "message": "Phase 1: Real git branch listing pending Phase 8 git_workspace_service.py.",
        "is_simulated": True,
    }


@router.post("/checkout")
async def git_checkout(req: GitCheckoutRequest, _user: User = Depends(get_current_user)):
    return {
        "status": "not_yet_implemented",
        "branch": req.branch,
        "message": "Phase 1: Real git checkout pending Phase 8 git_workspace_service.py.",
        "is_simulated": True,
    }


@router.post("/merge")
async def git_merge(req: GitMergeRequest, _user: User = Depends(get_current_user)):
    return {
        "status": "not_yet_implemented",
        "source": req.source_branch,
        "target": req.target_branch,
        "conflicts": 0,
        "message": "Phase 1: Real git merge pending Phase 8 git_workspace_service.py.",
        "is_simulated": True,
    }
