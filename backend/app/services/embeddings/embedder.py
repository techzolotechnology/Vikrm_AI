"""
Embedder Service: Provides Sentence Transformers embeddings using BAAI/bge-base-en-v1.5
with fallback to all-MiniLM-L6-v2 or CPU-friendly vector encoding.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
FALLBACK_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class CodeEmbedder:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._dimension = 768 if "bge-base" in model_name else 384

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading primary SentenceTransformer model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            self._dimension = self._model.get_sentence_embedding_dimension() or self._dimension
            return self._model
        except Exception as exc:
            logger.warning("Failed to load primary model %s: %s. Loading fallback %s", self.model_name, exc, FALLBACK_EMBEDDING_MODEL)
            try:
                from sentence_transformers import SentenceTransformer
                self.model_name = FALLBACK_EMBEDDING_MODEL
                self._model = SentenceTransformer(FALLBACK_EMBEDDING_MODEL)
                self._dimension = self._model.get_sentence_embedding_dimension() or 384
                return self._model
            except Exception as exc2:
                logger.warning("Failed to load fallback SentenceTransformer: %s. Using deterministic fallback vectorizer.", exc2)
                self._model = "fallback"
                self._dimension = 384
                return self._model

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []

        model = self._load_model()
        if model == "fallback":
            return [self._deterministic_vector(t, self._dimension) for t in texts]

        try:
            vectors = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return vectors.tolist()
        except Exception as exc:
            logger.error("Embedding generation failed: %s. Falling back to deterministic vectors.", exc)
            return [self._deterministic_vector(t, self._dimension) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self._dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @staticmethod
    def _deterministic_vector(text: str, dim: int = 384) -> List[float]:
        """CPU-friendly deterministic embedding vector generator for offline/test environments."""
        import hashlib
        import math

        vec = [0.0] * dim
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vec[idx] += val

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-6:
            vec = [v / norm for v in vec]
        else:
            vec[0] = 1.0
        return vec
