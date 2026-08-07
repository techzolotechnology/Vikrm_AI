"""
Terminal Sandbox API Router.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.api.deps import get_current_user
from app.models.user import User
from app.services.terminal_service import TerminalService

router = APIRouter(prefix="/terminal", tags=["Terminal"])


class ExecuteCommandRequest(BaseModel):
    command: str = Field(..., example="npm run build")
    cwd: str = Field(".", description="Working directory")


@router.post("/execute")
async def execute_terminal_command(
    req: ExecuteCommandRequest,
    _user: User = Depends(get_current_user),
):
    res = await TerminalService.execute_command(command_str=req.command, cwd=req.cwd)
    return res
