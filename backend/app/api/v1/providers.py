from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.services.llm.registry import available_providers

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("")
async def list_providers(_user: User = Depends(get_current_user)) -> dict[str, list[str]]:
    return {"providers": available_providers()}
