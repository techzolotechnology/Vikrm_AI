"""
Vector Store Service: High-performance vector database wrapper over ChromaDB.
Manages isolated collections for frameworks, languages, datasets, templates, and tech docs.
"""
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_TECH_COLLECTIONS = [
    "react", "nextjs", "vue", "angular", "fastapi", "springboot",
    "express", "node", "flutter", "docker", "kubernetes", "sql",
    "mongodb", "python", "java", "cpp", "csharp", "html", "css",
    "javascript", "typescript", "general_datasets", "templates", "docs"
]


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    persist_dir = getattr(settings, "CHROMA_PERSIST_DIR", "data/chroma_db")
    return chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


class MultiCollectionVectorStore:
    def __init__(self, collection_name: str = "general_datasets") -> None:
        self.client = get_chroma_client()
        self.collection_name = collection_name.lower().replace(".", "").replace("-", "")
        self._collection = None

    def get_collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=None,
            )
        return self._collection

    def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if not ids:
            return
        col = self.get_collection()
        col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        col = self.get_collection()
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }
        if where:
            kwargs["where"] = where
        if where_document:
            kwargs["where_document"] = where_document

        try:
            res = col.query(**kwargs)
        except Exception as exc:
            logger.warning("Vector query failed for collection %s: %s", self.collection_name, exc)
            return []

        matches = []
        if not res or not res.get("ids") or not res["ids"][0]:
            return matches

        ids = res["ids"][0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        for i in range(len(ids)):
            matches.append({
                "id": ids[i],
                "document": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else 0.0,
                "collection": self.collection_name,
            })
        return matches

    def count(self) -> int:
        try:
            return self.get_collection().count()
        except Exception:
            return 0

    def delete_where(self, where: Dict[str, Any]) -> None:
        try:
            self.get_collection().delete(where=where)
        except Exception as exc:
            logger.warning("Failed to delete_where in collection %s: %s", self.collection_name, exc)
