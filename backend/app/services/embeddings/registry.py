from app.core.config import settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.deterministic_provider import DeterministicEmbeddingProvider
from app.services.embeddings.sentence_transformer_provider import SentenceTransformerProvider

_PROVIDERS: dict[str, type[EmbeddingProvider]] = {
    "sentence-transformers": SentenceTransformerProvider,
    "deterministic": DeterministicEmbeddingProvider,
}

_instance_cache: dict[str, EmbeddingProvider] = {}


def get_embedding_provider(name: str | None = None) -> EmbeddingProvider:
    resolved_name = name or settings.EMBEDDING_PROVIDER
    if resolved_name not in _instance_cache:
        provider_cls = _PROVIDERS.get(resolved_name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown embedding provider '{resolved_name}'. Available: {', '.join(_PROVIDERS)}"
            )
        _instance_cache[resolved_name] = provider_cls()
    return _instance_cache[resolved_name]
