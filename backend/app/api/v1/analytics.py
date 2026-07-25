"""
Analytics endpoints — read-only aggregation over data every prior
milestone already persists. No new writes happen here.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import ActivityItem, DashboardStats
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> DashboardStats:
    service = AnalyticsService(db)
    return await service.get_dashboard_stats(user_id=user.id)


@router.get("/activity", response_model=list[ActivityItem])
async def get_recent_activity(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ActivityItem]:
    service = AnalyticsService(db)
    return await service.get_recent_activity(user_id=user.id, limit=limit)
