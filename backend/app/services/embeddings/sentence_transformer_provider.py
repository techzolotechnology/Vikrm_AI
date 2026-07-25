"""
Sentence-Transformers embedding provider — the real, production
implementation. Downloads model weights from Hugging Face on first use
(cached locally after that), which requires the container to have
outbound network access the first time it runs. Loaded lazily so
importing this module (e.g. for the registry) never triggers a
download by itself — only actually calling `.embed()` does.
"""
from app.core.config import settings
from app.services.embeddings.base import EmbeddingProvider

_MODEL_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
}


class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None  # lazy-loaded on first .embed() call

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.tolist()

    @property
    def dimensions(self) -> int:
        return _MODEL_DIMENSIONS.get(self.model_name, 384)
