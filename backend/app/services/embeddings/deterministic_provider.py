"""
Deterministic embedding provider.

Not a mock — this is a real, working embedding function (it produces
genuinely usable vectors that ChromaDB can index and query), just a
much cruder one than sentence-transformers: it hashes n-grams of each
text into a fixed-size vector, so texts sharing words end up with
non-trivial cosine similarity while being 100% offline and network-free.
Used in the test suite (see tests/conftest.py) to exercise the *real*
ChromaDB storage/retrieval pipeline without requiring a model download,
and available as a fallback via EMBEDDING_PROVIDER=deterministic for
fully offline development.
"""
import hashlib

from app.services.embeddings.base import EmbeddingProvider

_DIMENSIONS = 64


class DeterministicEmbeddingProvider(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * _DIMENSIONS
        words = text.lower().split()
        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            for i in range(_DIMENSIONS):
                vector[i] += digest[i % len(digest)] / 255.0
        norm = sum(v * v for v in vector) ** 0.5
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    @property
    def dimensions(self) -> int:
        return _DIMENSIONS
