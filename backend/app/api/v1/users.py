"""
User management and user preferences endpoints.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


class PreferencesRequest(BaseModel):
    theme: str | None = None
    accent_color: str | None = None
    reduce_animations: bool | None = None
    compact_sidebar: bool | None = None
    notifications: dict | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None


@router.get("", response_model=list[UserResponse])
async def list_users(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if body.full_name is not None:
        user.full_name = body.full_name
        await db.commit()
        await db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/me/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.get("/me/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    if user.preferences:
        try:
            return json.loads(user.preferences)
        except Exception:
            pass
    return {
        "theme": "dark",
        "accent_color": "#7C3AED",
        "reduce_animations": False,
        "compact_sidebar": False,
        "notifications": {
            "workflow_completion": True,
            "agent_activity": True,
            "system_health": True,
        },
    }


@router.patch("/me/preferences")
async def update_preferences(
    body: PreferencesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = {}
    if user.preferences:
        try:
            existing = json.loads(user.preferences)
        except Exception:
            pass
    
    updates = body.model_dump(exclude_unset=True)
    existing.update(updates)
    user.preferences = json.dumps(existing)
    await db.commit()
    return existing
