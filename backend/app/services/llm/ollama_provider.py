"""
Ollama provider with persistent HTTP client manager, process auto-spawning, health pre-flight, exponential backoff auto recovery, and stage logging.
"""
import asyncio
import json
import socket
import time
from typing import AsyncIterator, List, Dict, Any

import httpx
import httpcore

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import ChatMessage, LLMProvider, ProviderError, normalize_content_chunk
from app.services.llm.ollama_client_manager import ollama_client_manager, get_normalized_ollama_urls
from app.services.llm.ollama_process_manager import OllamaProcessManager

logger = get_logger(__name__)

# Broad tuple covering all socket, HTTPX, httpcore, and OS level network faults
NETWORK_ERRORS = (
    httpx.HTTPError,
    httpx.RequestError,
    httpx.ProtocolError,
    httpx.TransportError,
    httpcore.NetworkError,
    httpcore.ProtocolError,
    httpcore.RemoteProtocolError,
    httpcore.ConnectError,
    httpcore.WriteError,
    httpcore.ReadError,
    OSError,
    ConnectionError,
    socket.error,
    asyncio.TimeoutError,
)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str | None = None) -> None:
        self._is_custom_url = base_url is not None
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    async def list_installed_models(self) -> List[Dict[str, Any]]:
        """Fetch installed models from Ollama via OllamaClientManager."""
        return await ollama_client_manager.fetch_installed_models(self.base_url)

    async def chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> str:
        """Non-streaming chat completion."""
        full_text = []
        async for chunk in self.stream_chat(messages=messages, model=model, temperature=temperature):
            full_text.append(chunk)
        return "".join(full_text)

    async def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        start_time = time.perf_counter()
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }

        logger.info("[Incoming Request] Starting Ollama stream_chat for model=%s (messages=%d)", model, len(messages))

        # 1. Pre-flight Health Check & Process Check
        healthy_target_url = await ollama_client_manager.ping_health(self.base_url)
        
        target_urls = get_normalized_ollama_urls(self.base_url)
        if healthy_target_url:
            if healthy_target_url in target_urls:
                target_urls.remove(healthy_target_url)
            target_urls.insert(0, healthy_target_url)

        connected = False
        total_tokens = 0
        last_exception: Exception | None = None
        
        # Exponential backoff schedule: 1s, 2s, 4s, 8s, 16s (Phase 4 requirement)
        backoff_delays = [1.0, 2.0, 4.0, 8.0, 16.0]

        for target_url in target_urls:
            endpoint = f"{target_url}/api/chat"
            logger.info("[Ollama Request] Invoking endpoint POST %s (model: %s)", endpoint, model)

            for attempt, delay in enumerate(backoff_delays):
                try:
                    client = await ollama_client_manager.get_client()
                    
                    async with client.stream("POST", endpoint, json=payload) as response:
                        if response.status_code == 404:
                            logger.warning("[Recovery Failure] Model '%s' returned HTTP 404 at %s", model, target_url)
                            await ollama_client_manager.trigger_auto_pull(model, target_url)
                            raise ProviderError(
                                f"Model '{model}' not found on Ollama at {target_url}. "
                                f"Run `ollama pull {model}` in your terminal."
                            )

                        response.raise_for_status()
                        connected = True
                        logger.info("[Recovery Success] Connected to Ollama at %s on attempt %d", endpoint, attempt + 1)

                        async for line in response.aiter_lines():
                            line_str = line.strip()
                            if not line_str:
                                continue
                            try:
                                chunk = json.loads(line_str)
                            except json.JSONDecodeError as err:
                                logger.warning("[OllamaProvider] Failed parsing JSON line: %s", err)
                                continue

                            if chunk.get("error"):
                                raise ProviderError(f"Ollama error: {chunk['error']}")

                            # ─── ROOT CAUSE FIX ───────────────────────────────────────────────────────
                            # BEFORE (BUG): chunk.get("message") returns the FULL DICT when content=""
                            # e.g. {"role": "assistant", "content": ""} → coerces to [object Object]
                            # in the browser when concatenated into the streaming string.
                            # AFTER  (FIX): only ever extract the string content field from the
                            # message dict. If that field is missing or empty, skip the chunk.
                            message_obj = chunk.get("message")
                            if isinstance(message_obj, dict):
                                raw_content = message_obj.get("content") or ""
                            else:
                                # Fallback for old /api/generate style responses
                                raw_content = chunk.get("response") or ""

                            if not isinstance(raw_content, str):
                                raw_content = str(raw_content)

                            if raw_content:
                                norm_str = normalize_content_chunk(raw_content)
                                if norm_str:
                                    if total_tokens == 0:
                                        logger.info("[Streaming Started] Yielding first token from %s", endpoint)
                                    total_tokens += 1
                                    yield norm_str

                            if chunk.get("done", False):
                                logger.info("[Streaming Finished] Stream completed cleanly from %s (tokens=%d)", endpoint, total_tokens)
                                break
                        break

                except NETWORK_ERRORS as exc:
                    last_exception = exc
                    if isinstance(exc, (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException, asyncio.TimeoutError)):
                        logger.warning("[Timeout] Attempt %d timed out for %s: %s", attempt + 1, endpoint, exc)
                    else:
                        logger.warning("[Retry Attempt] Attempt %d network exception for %s: %s", attempt + 1, endpoint, exc)

                    # Auto-recover process & recreate HTTP client pool if no tokens streamed yet
                    if total_tokens == 0 and attempt < len(backoff_delays) - 1:
                        logger.info("[Auto Recovery] Triggering process manager & HTTP pool recreation before delay %.1fs", delay)
                        await OllamaProcessManager.ensure_ollama_running()
                        await ollama_client_manager.get_client(force_recreate=True)
                        await asyncio.sleep(delay)
                        continue
                    elif total_tokens > 0:
                        logger.warning("[Streaming Interrupted] Stream interrupted after %d tokens yielded: %s", total_tokens, exc)
                        break

                except ProviderError:
                    raise
                except asyncio.CancelledError:
                    logger.warning("[Streaming Cancelled] Ollama stream task cancelled for %s", endpoint)
                    raise
                except Exception as exc:
                    last_exception = exc
                    logger.exception("[Streaming Failed] Unhandled exception streaming from %s: %s", endpoint, exc)
                    if total_tokens == 0 and attempt < len(backoff_delays) - 1:
                        await OllamaProcessManager.ensure_ollama_running()
                        await ollama_client_manager.get_client(force_recreate=True)
                        await asyncio.sleep(delay)
                        continue
                    break

            if connected:
                break

        elapsed = time.perf_counter() - start_time

        if not connected:
            logger.error("[Recovery Failure] All connection attempts failed for Ollama (%s)", last_exception)
            # Try configured external fallback API keys if available
            if settings.GROQ_API_KEY:
                from app.services.llm.external_providers import GroqProvider
                logger.info("[Auto Recovery] Ollama unreachable (%s). Delegating stream to GroqProvider.", last_exception)
                async for chunk in GroqProvider().stream_chat(messages=messages, model="llama-3.3-70b-versatile", temperature=temperature):
                    yield chunk
                return

            if settings.OPENAI_API_KEY:
                from app.services.llm.external_providers import OpenAIProvider
                logger.info("[Auto Recovery] Ollama unreachable (%s). Delegating stream to OpenAIProvider.", last_exception)
                async for chunk in OpenAIProvider().stream_chat(messages=messages, model="gpt-4o", temperature=temperature):
                    yield chunk
                return

            if settings.GEMINI_API_KEY:
                from app.services.llm.external_providers import GeminiProvider
                logger.info("[Auto Recovery] Ollama unreachable (%s). Delegating stream to GeminiProvider.", last_exception)
                async for chunk in GeminiProvider().stream_chat(messages=messages, model="gemini-2.0-flash", temperature=temperature):
                    yield chunk
                return

            if settings.ANTHROPIC_API_KEY:
                from app.services.llm.external_providers import AnthropicProvider
                logger.info("[Auto Recovery] Ollama unreachable (%s). Delegating stream to AnthropicProvider.", last_exception)
                async for chunk in AnthropicProvider().stream_chat(messages=messages, model="claude-3-5-sonnet", temperature=temperature):
                    yield chunk
                return

            if settings.OPENROUTER_API_KEY:
                from app.services.llm.external_providers import OpenRouterProvider
                logger.info("[Auto Recovery] Ollama unreachable (%s). Delegating stream to OpenRouterProvider.", last_exception)
                async for chunk in OpenRouterProvider().stream_chat(messages=messages, model="openrouter/auto", temperature=temperature):
                    yield chunk
                return

            # Connection failed & no cloud keys configured
            raise ProviderError(
                f"Could not connect to Ollama at {self.base_url} ({last_exception}). "
                "Ensure Ollama for Windows is running locally."
            )

        logger.info(
            "[Streaming Finished] Final Response Streamed: model=%s tokens=%d latency=%.2fs",
            model,
            total_tokens,
            elapsed,
        )
