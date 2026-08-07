"""
Provider registry.

Adding OpenAI/Anthropic/Gemini/Groq/etc in a later milestone means
adding one class + one line here — `ChatService` and the API layer
never change.
"""
from app.services.llm.base import LLMProvider, ProviderError
from app.services.llm.external_providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenAIProvider,
    OpenRouterProvider,
    QwenProvider,
)
from app.services.llm.ollama_provider import OllamaProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
    "deepseek": DeepSeekProvider,
    "mistral": MistralProvider,
    "qwen": QwenProvider,
}


def get_provider(name: str) -> LLMProvider:
    provider_cls = _PROVIDERS.get(name.lower().strip())
    if provider_cls is None:
        raise ProviderError(
            f"Unknown provider '{name}'. Available: {', '.join(_PROVIDERS)}"
        )
    return provider_cls()


def available_providers() -> list[str]:
    return list(_PROVIDERS.keys())
