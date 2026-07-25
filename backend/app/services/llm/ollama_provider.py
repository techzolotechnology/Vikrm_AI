"""
Ollama provider.

Talks to Ollama's `/api/chat` streaming endpoint, which returns
newline-delimited JSON objects (one per chunk), not SSE. We parse each
line as it arrives and yield the incremental `message.content` text.
This is a real HTTP streaming client, not a wrapper around a blocking call.
"""
import json
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import ChatMessage, LLMProvider, ProviderError

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    async def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/chat", json=payload
                ) as response:
                    if response.status_code == 404:
                        raise ProviderError(
                            f"Model '{model}' not found on Ollama. "
                            f"Pull it first with: ollama pull {model}"
                        )
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        chunk = json.loads(line)
                        if chunk.get("error"):
                            raise ProviderError(chunk["error"])
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
        except httpx.ConnectError as exc:
            raise ProviderError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Is Ollama running? (default local install: `ollama serve`)"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Ollama returned an error: {exc.response.text}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("Received a malformed response from Ollama") from exc
