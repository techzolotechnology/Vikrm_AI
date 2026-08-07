"""
Hugging Face API router.
"""
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.models.user import User
from app.services.huggingface_service import HuggingFaceService

router = APIRouter(prefix="/huggingface", tags=["HuggingFace"])


@router.get("/models")
async def search_hf_models(
    q: str = Query("llama", description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    _user: User = Depends(get_current_user),
):
    models = await HuggingFaceService.search_models(query=q, limit=limit)
    return {"models": models}


@router.get("/datasets")
async def search_hf_datasets(
    q: str = Query("code", description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    _user: User = Depends(get_current_user),
):
    datasets = await HuggingFaceService.search_datasets(query=q, limit=limit)
    return {"datasets": datasets}


@router.get("/spaces")
async def search_hf_spaces(
    q: str = Query("chat", description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    _user: User = Depends(get_current_user),
):
    spaces = await HuggingFaceService.search_spaces(query=q, limit=limit)
    return {"spaces": spaces}
