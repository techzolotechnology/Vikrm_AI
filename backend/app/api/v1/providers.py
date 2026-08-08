from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel, Field

from app.core.config import settings
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


def get_configured_providers_dict() -> tuple[dict[str, list[str]], bool]:
    """Helper to return configured models grouped by provider, plus ollama health."""
    ollama_models = []
    ollama_online = False
    try:
        provider = OllamaProvider()
        import asyncio
        # Run sync/async call safely
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In async context
            pass
    except Exception:
        pass

    return {}, False

@router.get("")
async def list_providers(_user: User = Depends(get_current_user)) -> dict[str, list[str]]:
    models_data = await list_all_models(_user=_user)
    return {"providers": list(models_data["providers"].keys())}


@router.get("/models")
async def list_all_models(_user: User = Depends(get_current_user)):
    """Returns supported models grouped by provider for currently configured providers."""
    ollama_models = []
    ollama_online = False
    try:
        provider = OllamaProvider()
        ollama_models = await provider.list_installed_models()
        ollama_online = True
    except Exception:
        ollama_online = False
        ollama_models = ["qwen3:8b"]

    configured_providers: dict[str, list[str]] = {
        "ollama": ollama_models or ["qwen3:8b"]
    }

    CLOUD_CATALOG = {
        "openai": (settings.OPENAI_API_KEY, ["gpt-4o", "gpt-4-turbo", "o1", "o3-mini"]),
        "anthropic": (settings.ANTHROPIC_API_KEY, ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]),
        "gemini": (settings.GEMINI_API_KEY, ["gemini-1.5-pro", "gemini-2.0-flash"]),
        "groq": (settings.GROQ_API_KEY, ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b"]),
        "openrouter": (settings.OPENROUTER_API_KEY, ["openrouter/auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o"]),
        "deepseek": (settings.DEEPSEEK_API_KEY, ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]),
        "qwen": (settings.QWEN_API_KEY, ["qwen-max", "qwen-coder-turbo"]),
        "mistral": (settings.MISTRAL_API_KEY, ["mistral-large-latest", "codestral-latest"]),
    }

    for name, (api_key, models) in CLOUD_CATALOG.items():
        if api_key and api_key.strip():
            configured_providers[name] = models

    return {
        "providers": configured_providers,
        "ollama_online": ollama_online
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
