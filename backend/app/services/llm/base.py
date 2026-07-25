"""
LLM provider abstraction.

Every provider (Ollama now; OpenAI/Anthropic/Gemini/Groq/etc in later
milestones) implements this single interface: an async generator that
yields text chunks. This is the seam that lets `ChatService` stay
provider-agnostic — it never imports a provider-specific SDK directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class ProviderError(Exception):
    """Raised when a provider fails to stream a response (unreachable,
    model not found, malformed response, etc)."""


class LLMProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Yields response text chunks as they become available."""
        raise NotImplementedError
