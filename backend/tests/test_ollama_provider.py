"""
Tests the actual HTTP streaming parse logic in OllamaProvider against
`mock_ollama_server` (defined in conftest.py) — a real ASGI server
speaking Ollama's exact newline-delimited-JSON streaming protocol.
This exercises the real httpx streaming code path, not a mocked
provider — only the far end (a real Ollama installation) is substituted.
"""
import pytest

from app.services.llm.base import ChatMessage, ProviderError
from app.services.llm.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_provider_streams_real_chunks(mock_ollama_server: str) -> None:
    provider = OllamaProvider(base_url=mock_ollama_server)
    chunks = []
    async for chunk in provider.stream_chat(
        messages=[ChatMessage(role="user", content="hi")], model="llama3.2"
    ):
        chunks.append(chunk)

    assert chunks == ["Hello", " there", "!"]


@pytest.mark.asyncio
async def test_ollama_provider_unreachable_raises_provider_error() -> None:
    provider = OllamaProvider(base_url="http://127.0.0.1:1")  # nothing listens here
    with pytest.raises(ProviderError, match="Could not connect"):
        async for _ in provider.stream_chat(
            messages=[ChatMessage(role="user", content="hi")], model="llama3.2"
        ):
            pass
