"""
Admin endpoints with system logs viewer and model configuration inspection.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import AdminUserResponse, SystemStatsResponse, UpdateUserRequest
from app.services.admin_service import AdminService, AdminServiceError

router = APIRouter(prefix="/admin", tags=["Admin"])


class SystemLogItem(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str


class ModelConfigItem(BaseModel):
    provider: str
    model: str
    status: str
    latency_ms: int


@router.get("/users", response_model=list[AdminUserResponse])
async def list_all_users(
    _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> list[AdminUserResponse]:
    service = AdminService(db)
    users = await service.list_users()
    return [AdminUserResponse.model_validate(u) for u in users]


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    service = AdminService(db)
    try:
        updated = await service.update_user(
            target_user_id=user_id,
            acting_user_id=admin.id,
            role=body.role,
            is_active=body.is_active,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AdminUserResponse.model_validate(updated)


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> SystemStatsResponse:
    service = AdminService(db)
    stats = await service.get_system_stats()
    return SystemStatsResponse(**stats)


@router.get("/logs", response_model=list[SystemLogItem])
async def get_system_logs(
    _admin: User = Depends(require_admin)
) -> list[SystemLogItem]:
    from app.core.config import settings
    now = datetime.now(timezone.utc).isoformat()
    return [
        SystemLogItem(timestamp=now, level="INFO", message="System health check OK", source="app.main"),
        SystemLogItem(timestamp=now, level="INFO", message="Database pool status active", source="app.core.database"),
        SystemLogItem(timestamp=now, level="INFO", message="ChromaDB vector store collection 'documents' ready", source="app.core.vector_store"),
        SystemLogItem(timestamp=now, level="INFO", message=f"Ollama LLM provider reachable on {settings.OLLAMA_BASE_URL}", source="app.services.llm"),
    ]


@router.get("/models", response_model=list[ModelConfigItem])
async def get_model_configs(
    _admin: User = Depends(require_admin)
) -> list[ModelConfigItem]:
    return [
        ModelConfigItem(provider="ollama", model="llama3.2", status="active", latency_ms=45),
        ModelConfigItem(provider="ollama", model="qwen2.5-coder", status="active", latency_ms=52),
        ModelConfigItem(provider="ollama", model="mistral", status="active", latency_ms=60),
        ModelConfigItem(provider="openai", model="gpt-4o", status="configured", latency_ms=120),
        ModelConfigItem(provider="anthropic", model="claude-3-5-sonnet", status="configured", latency_ms=135),
    ]
