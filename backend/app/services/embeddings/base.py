"""
Embedding provider abstraction — mirrors `LLMProvider` (app/services/llm/base.py):
one interface, swappable implementations, so ChromaDB integration code
never depends on a specific embedding model or library.
"""
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Returns one embedding vector per input text, same order."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError
