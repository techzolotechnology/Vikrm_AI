"""
Datasets & RAG API Router: Exposes dataset management and RAG retrieval endpoints.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user

from app.models.user import User
from app.services.datasets.dataset_manager import DatasetManager
from app.services.rag.retriever import KnowledgeRetriever
from app.services.rag.context_builder import RAGContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["datasets", "rag"])
_manager_instance: Optional[DatasetManager] = None
_retriever_instance: Optional[KnowledgeRetriever] = None


def get_dataset_manager() -> DatasetManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DatasetManager()
    return _manager_instance


def get_knowledge_retriever() -> KnowledgeRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = KnowledgeRetriever()
    return _retriever_instance


class DownloadDatasetRequest(BaseModel):
    dataset_name: str = Field(..., description="Dataset name (e.g. code_search_net, CodeAlpaca_20K, MBPP)")
    force: bool = Field(False, description="Force re-download even if cached")


class UpdateDatasetRequest(BaseModel):
    dataset_name: Optional[str] = Field(None, description="Specific dataset or all if empty")
    force: bool = Field(False)


class ReindexDatasetRequest(BaseModel):
    dataset_name: str = Field(...)


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Coding question, application request, or bug report")
    top_k: int = Field(10, ge=1, le=50)


@router.get("/datasets")
async def list_datasets(
    current_user: User = Depends(get_current_user),

    manager: DatasetManager = Depends(get_dataset_manager),
) -> Dict[str, Any]:
    """Lists all supported Hugging Face datasets and their local caching/indexing status."""
    datasets = manager.list_datasets()
    stats = manager.vector_db.get_statistics()
    return {
        "status": "success",
        "datasets": datasets,
        "vector_statistics": stats,
    }


@router.post("/datasets/download")
async def download_dataset(
    req: DownloadDatasetRequest,
    current_user: User = Depends(get_current_user),

    manager: DatasetManager = Depends(get_dataset_manager),
) -> Dict[str, Any]:
    """Downloads and indexes a Hugging Face dataset."""
    try:
        res = manager.download_and_index(req.dataset_name, force=req.force)
        return {"status": "success", "data": res}
    except Exception as exc:
        logger.error("Failed to download dataset %s: %s", req.dataset_name, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download dataset: {exc}",
        )


@router.post("/datasets/update")
async def update_datasets(
    req: UpdateDatasetRequest,
    current_user: User = Depends(get_current_user),

    manager: DatasetManager = Depends(get_dataset_manager),
) -> Dict[str, Any]:
    """Triggers weekly version check and incremental reindexing for updated datasets."""
    try:
        if req.dataset_name:
            res = manager.updater.update_dataset(req.dataset_name, force=req.force)
        else:
            res = manager.update_all(force=req.force)
        return {"status": "success", "data": res}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update datasets: {exc}",
        )


@router.post("/datasets/reindex")
async def reindex_dataset(
    req: ReindexDatasetRequest,
    current_user: User = Depends(get_current_user),

    manager: DatasetManager = Depends(get_dataset_manager),
) -> Dict[str, Any]:
    """Rebuilds vector embeddings for a given dataset."""
    try:
        res = manager.reindex_dataset(req.dataset_name)
        return {"status": "success", "data": res}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {exc}",
        )


@router.delete("/datasets/{dataset_name}")
async def delete_dataset(
    dataset_name: str,
    current_user: User = Depends(get_current_user),

    manager: DatasetManager = Depends(get_dataset_manager),
) -> Dict[str, Any]:
    """Deletes a local dataset and removes its vector entries."""
    res = manager.delete_dataset(dataset_name)
    return {"status": "success", "data": res}


@router.get("/rag/search")
async def rag_search_get(
    query: str,
    top_k: int = 10,
    current_user: User = Depends(get_current_user),

    retriever: KnowledgeRetriever = Depends(get_knowledge_retriever),
) -> Dict[str, Any]:
    """GET endpoint for testing RAG retrieval engine."""
    results = retriever.retrieve_context(query, top_k=top_k)
    return {"status": "success", "results": results}


@router.post("/rag/query")
async def rag_query_post(
    req: RAGQueryRequest,
    current_user: User = Depends(get_current_user),

    retriever: KnowledgeRetriever = Depends(get_knowledge_retriever),
) -> Dict[str, Any]:
    """POST endpoint for executing RAG context generation."""
    results = retriever.retrieve_context(req.query, top_k=req.top_k)
    context_builder = RAGContextBuilder()
    augmented_prompt = context_builder.build_augmented_prompt(req.query, results)
    return {
        "status": "success",
        "query": req.query,
        "retrieval": results,
        "augmented_prompt": augmented_prompt,
    }
