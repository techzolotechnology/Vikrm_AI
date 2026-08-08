from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.registry import available_providers, get_provider
from app.services.llm.router import ModelRouter

router = APIRouter(prefix="/providers", tags=["Providers"])


class RouteRequest(BaseModel):
    task: str = Field(..., description="Task description or prompt")
    intent: str | None = None
    offline: bool = False
    free_mode: bool = False
    manual_provider: str | None = None
    manual_model: str | None = None


@router.get("")
async def list_providers(_user: User = Depends(get_current_user)) -> dict[str, list[str]]:
    return {"providers": available_providers()}


@router.get("/models")
async def list_all_models(_user: User = Depends(get_current_user)):
    """Returns supported models grouped by provider."""
    ollama_models = []
    try:
        provider = OllamaProvider()
        ollama_models = await provider.list_installed_models()
    except Exception:
        ollama_models = ["qwen3:8b", "llama3", "codellama", "mistral"]

    return {
        "providers": {
            "openai": ["gpt-4o", "gpt-4-turbo", "o1", "o3-mini"],
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "gemini": ["gemini-1.5-pro", "gemini-2.0-flash"],
            "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b"],
            "ollama": ollama_models or ["qwen3:8b"],
            "openrouter": ["openrouter/auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o"],
            "deepseek": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
            "qwen": ["qwen-max", "qwen-coder-turbo"],
            "mistral": ["mistral-large-latest", "codestral-latest"],
        }
    }


@router.get("/ollama/models")
async def list_ollama_models(_user: User = Depends(get_current_user)):
    provider = OllamaProvider()
    models = await provider.list_installed_models()
    return {"models": models}


@router.post("/route")
async def route_task(req: RouteRequest, _user: User = Depends(get_current_user)):
    """Determines optimal provider and model based on intent and task."""
    decision = ModelRouter.route_task(
        task_description=req.task,
        intent=req.intent,
        offline=req.offline,
        free_mode=req.free_mode,
        manual_override_provider=req.manual_provider,
        manual_override_model=req.manual_model,
    )
    return {
        "provider": decision.provider,
        "model": decision.model,
        "reason": decision.reason,
    }
