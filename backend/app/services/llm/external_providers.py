"""
External LLM providers.

Implements streaming chat completion for:
- OpenAI (gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
- Anthropic (claude-3-5-sonnet, claude-3-opus)
- Gemini (gemini-1.5-pro, gemini-2.0-flash)
- Groq (llama-3.3-70b-versatile, mixtral-8x7b)
- OpenRouter (openrouter/auto)
- DeepSeek (deepseek-chat, deepseek-coder, deepseek-reasoner)
- Mistral (mistral-large-latest, mistral-small-latest)

Each provider verifies API key availability, streams responses using raw `httpx.AsyncClient`
with SSE parsing, and translates HTTP/status/authentication errors into clean `ProviderError` instances.
"""
import json
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import ChatMessage, LLMProvider, ProviderError, normalize_content_chunk

logger = get_logger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """Base provider for OpenAI-compatible chat completion endpoints."""

    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        api_key_getter: callable,
        default_model: str,
    ) -> None:
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key_getter = api_key_getter
        self.default_model = default_model

    async def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        api_key = self.api_key_getter()
        if not api_key:
            raise ProviderError(
                f"{self.provider_name.capitalize()} API key is not configured. "
                f"Set {self.provider_name.upper()}_API_KEY in your environment."
            )

        resolved_model = model or self.default_model
        payload = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/chat/completions", json=payload, headers=headers
                ) as response:
                    if response.status_code == 401:
                        raise ProviderError(f"Invalid API key for {self.provider_name}.")
                    if response.status_code == 404:
                        raise ProviderError(f"Model '{resolved_model}' not found on {self.provider_name}.")
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        trimmed = line.strip()
                        if not trimmed or trimmed == "data: [DONE]":
                            continue
                        if trimmed.startswith("data:"):
                            raw_json = trimmed[5:].strip()
                            try:
                                chunk = json.loads(raw_json)
                                delta = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if delta:
                                    norm_delta = normalize_content_chunk(delta)
                                    if norm_delta:
                                        yield norm_delta
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError as exc:
            raise ProviderError(
                f"Could not connect to {self.provider_name} at {self.base_url}."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"{self.provider_name.capitalize()} returned status {exc.response.status_code}: {exc.response.text}"
            ) from exc


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name="openai",
            base_url="https://api.openai.com/v1",
            api_key_getter=lambda: settings.OPENAI_API_KEY,
            default_model="gpt-4o",
        )


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key_getter=lambda: settings.GROQ_API_KEY,
            default_model="llama-3.3-70b-versatile",
        )


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key_getter=lambda: settings.OPENROUTER_API_KEY,
            default_model="openrouter/auto",
        )


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name="deepseek",
            base_url="https://api.deepseek.com/v1",
            api_key_getter=lambda: settings.DEEPSEEK_API_KEY,
            default_model="deepseek-chat",
        )


class MistralProvider(OpenAICompatibleProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name="mistral",
            base_url="https://api.mistral.ai/v1",
            api_key_getter=lambda: getattr(settings, "MISTRAL_API_KEY", None),
            default_model="mistral-large-latest",
        )


class QwenProvider(OpenAICompatibleProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name="qwen",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_getter=lambda: getattr(settings, "QWEN_API_KEY", None),
            default_model="qwen-max",
        )


class AnthropicProvider(LLMProvider):
    async def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ProviderError(
                "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in your environment."
            )

        system_prompt = None
        formatted_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                formatted_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model or "claude-3-5-sonnet-20241022",
            "messages": formatted_messages,
            "max_tokens": 4096,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream(
                    "POST", "https://api.anthropic.com/v1/messages", json=payload, headers=headers
                ) as response:
                    if response.status_code == 401:
                        raise ProviderError("Invalid API key for Anthropic.")
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        trimmed = line.strip()
                        if trimmed.startswith("data:"):
                            raw_json = trimmed[5:].strip()
                            try:
                                chunk = json.loads(raw_json)
                                event_type = chunk.get("type")
                                if event_type == "content_block_delta":
                                    text = chunk.get("delta", {}).get("text", "")
                                    if text:
                                        norm_text = normalize_content_chunk(text)
                                        if norm_text:
                                            yield norm_text
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError as exc:
            raise ProviderError("Could not connect to Anthropic API.") from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Anthropic API returned status {exc.response.status_code}: {exc.response.text}"
            ) from exc


class GeminiProvider(LLMProvider):
    async def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ProviderError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in your environment."
            )

        resolved_model = model or "gemini-1.5-pro"
        contents = []
        for m in messages:
            role = "user" if m.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{resolved_model}:streamGenerateContent?key={api_key}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code in (401, 403):
                        raise ProviderError("Invalid or unauthorized API key for Google Gemini.")
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        trimmed = line.strip()
                        if trimmed.startswith("data:"):
                            raw_json = trimmed[5:].strip()
                            try:
                                chunk = json.loads(raw_json)
                                candidates = chunk.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        text = part.get("text", "")
                                        if text:
                                            norm_text = normalize_content_chunk(text)
                                            if norm_text:
                                                yield norm_text
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError as exc:
            raise ProviderError("Could not connect to Google Gemini API.") from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Gemini API returned status {exc.response.status_code}: {exc.response.text}"
            ) from exc
