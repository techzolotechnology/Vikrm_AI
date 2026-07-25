"""
Admin endpoints — every route requires `require_admin` (Milestone 2's
RBAC dependency). Non-admins get a 403 before any service code runs.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import AdminUserResponse, SystemStatsResponse, UpdateUserRequest
from app.services.admin_service import AdminService, AdminServiceError

router = APIRouter(prefix="/admin", tags=["Admin"])


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
