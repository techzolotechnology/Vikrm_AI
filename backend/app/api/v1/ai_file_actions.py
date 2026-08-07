"""
AI File Actions API — Phase 5 of Professional AI IDE
Provides per-file LLM-powered actions: explain, refactor, optimize, document,
test_generate, fix_bugs, code_review, security_scan, translate, extract_component, extract_function
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai_file_action_service import AIFileActionService

router = APIRouter(prefix="/ai-actions", tags=["AI File Actions"])


class FileActionRequest(BaseModel):
    action: str = Field(..., example="refactor")
    path: str = Field(..., example="src/components/App.tsx")
    content: str = Field(..., description="File content (max 8000 chars)")
    language: str = Field("typescript", description="Programming language")
    provider: str = Field("ollama", description="LLM provider")
    model: str = Field("llama3.2", description="Model name")


@router.post("/execute")
async def execute_file_action(
    req: FileActionRequest,
    user: User = Depends(get_current_user),
):
    """
    Execute an AI action on a single file.
    Returns the transformed/analyzed result.
    """
    result = await AIFileActionService.execute_action(
        action=req.action,
        path=req.path,
        content=req.content,
        language=req.language,
        provider_name=req.provider,
        model=req.model,
    )
    return result
