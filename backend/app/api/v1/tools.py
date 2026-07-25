"""
Tool endpoints: listing, direct standalone execution (with logging),
and execution history.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.tool import ExecuteToolRequest, ToolExecutionResponse
from app.services.tool_execution_service import ToolExecutionService
from app.services.tools.registry import list_tools

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("")
async def list_available_tools(_user: User = Depends(get_current_user)) -> list[dict]:
    return list_tools()


@router.post("/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_name: str,
    body: ExecuteToolRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ToolExecutionResponse:
    service = ToolExecutionService(db)
    execution = await service.execute(user_id=user.id, tool_name=tool_name, input_text=body.input)
    return ToolExecutionResponse.model_validate(execution)


@router.get("/executions/history", response_model=list[ToolExecutionResponse])
async def get_execution_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ToolExecutionResponse]:
    service = ToolExecutionService(db)
    history = await service.list_history(user_id=user.id)
    return [ToolExecutionResponse.model_validate(e) for e in history]
