"""
Vector store wrapper around ChromaDB.

Runs embedded (PersistentClient writing to a local directory) rather
than as a separate server — consistent with the project's local-first
philosophy and avoiding an extra network hop for every memory/RAG
lookup. `VectorStore` never calls ChromaDB's own embedding functions;
embeddings are always computed explicitly via an `EmbeddingProvider`
first and passed in, so the same embedding logic is used consistently
for both memory (Milestone 5) and document RAG (Milestone 6).
"""
from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings


from chromadb.config import Settings as ChromaSettings


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )



class VectorStore:
    def __init__(self, collection_name: str) -> None:
        self._client = get_chroma_client()
        self._collection_name = collection_name

    def _collection(self) -> Collection:
        # embedding_function=None: we always pass precomputed vectors,
        # never raw documents, to `.add`/`.query`.
        return self._client.get_or_create_collection(
            self._collection_name, embedding_function=None
        )

    def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._collection().upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def query(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        where: dict | None = None,
    ) -> list[dict]:
        result = self._collection().query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        matches = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for i in range(len(ids)):
            matches.append(
                {
                    "id": ids[i],
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                }
            )
        return matches

    def delete(self, ids: list[str]) -> None:
        self._collection().delete(ids=ids)

    def delete_where(self, where: dict) -> None:
        self._collection().delete(where=where)
