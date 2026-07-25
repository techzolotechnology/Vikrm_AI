import pytest
from app.services.llm.base import ProviderError
from app.services.llm.registry import available_providers, get_provider


def test_available_providers_list():
    providers = available_providers()
    assert "ollama" in providers
    assert "openai" in providers
    assert "anthropic" in providers
    assert "gemini" in providers
    assert "groq" in providers
    assert "openrouter" in providers
    assert "deepseek" in providers
    assert "mistral" in providers


@pytest.mark.asyncio
async def test_external_providers_missing_api_key_raises():
    for name in ["openai", "anthropic", "gemini", "groq", "openrouter", "deepseek", "mistral"]:
        provider = get_provider(name)
        with pytest.raises(ProviderError) as exc_info:
            async for _chunk in provider.stream_chat(messages=[], model="test"):
                pass
        assert "API key" in str(exc_info.value)
