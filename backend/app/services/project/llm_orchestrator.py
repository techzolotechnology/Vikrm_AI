"""
Centralized LLM Orchestrator Service.
Provides robust multi-provider calling, exponential retry backoff, and JSON schema extraction.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.services.llm.base import ChatMessage
from app.services.llm.registry import get_provider
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class ProviderError(Exception):
    """Raised when an LLM provider invocation fails."""
    pass


class LLMOrchestrator:
    def __init__(
        self,
        default_provider: str = "ollama",
        default_model: str = "",
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        self.default_provider = default_provider
        self.default_model = default_model
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def chat(
        self,
        messages: List[ChatMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        prov_name = provider_name or self.default_provider
        mdl = model or self.default_model
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                provider = get_provider(prov_name)
                response = await provider.chat(messages=messages, model=mdl, temperature=temperature)
                if response and response.strip():
                    return response
                raise ProviderError(f"Empty response received from provider '{prov_name}'")
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "[LLMOrchestrator] Attempt %d/%d failed for provider '%s': %s",
                    attempt,
                    self.max_retries,
                    prov_name,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.backoff_factor * (2 ** (attempt - 1)))

        raise ProviderError(f"All {self.max_retries} attempts failed for LLMOrchestrator: {last_error}")

    async def chat_structured(
        self,
        messages: List[ChatMessage],
        schema_model: Type[T],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """
        Invoices LLM and parses structured JSON matching pydantic schema_model.
        """
        system_instruction = (
            f"\n\nYou MUST respond with valid raw JSON matching this JSON Schema:\n"
            f"```json\n{json.dumps(schema_model.model_json_schema(), indent=2)}\n```\n"
            f"Do not include any intro, conversational text, or markdown text outside the JSON block."
        )
        augmented_messages = list(messages)
        if augmented_messages and augmented_messages[0].role == "system":
            augmented_messages[0] = ChatMessage(
                role="system", content=augmented_messages[0].content + system_instruction
            )
        else:
            augmented_messages.insert(0, ChatMessage(role="system", content=system_instruction.strip()))

        raw_response = await self.chat(
            messages=augmented_messages,
            provider_name=provider_name,
            model=model,
            temperature=temperature,
        )

        # Extract JSON substring
        json_str = raw_response.strip()
        if "```" in json_str:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str)
            if match:
                json_str = match.group(1).strip()

        try:
            data = json.loads(json_str)
            return schema_model.model_validate(data)
        except Exception as exc:
            logger.warning("[LLMOrchestrator] Failed parsing structured JSON output: %s", exc)
            # Try fuzzy JSON cleanup
            match = re.search(r"\{[\s\S]*\}", json_str)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return schema_model.model_validate(data)
                except Exception:
                    pass
            raise ProviderError(f"Failed to parse response into model {schema_model.__name__}: {exc}\nRaw: {json_str[:200]}")
