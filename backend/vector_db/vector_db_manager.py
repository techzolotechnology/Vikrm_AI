"""
Vector Database Manager: Manages initialization, collection statistics, and unified query routing
across all tech vector collections (React, Next.js, Vue, FastAPI, Spring Boot, Docker, etc.).
"""
import logging
from typing import Any, Dict, List, Optional

from app.services.embeddings.embedder import CodeEmbedder
from app.services.embeddings.vector_store import MultiCollectionVectorStore, SUPPORTED_TECH_COLLECTIONS

logger = logging.getLogger(__name__)


class VectorDBManager:
    def __init__(self) -> None:
        self.embedder = CodeEmbedder()
        self.stores: Dict[str, MultiCollectionVectorStore] = {
            tech: MultiCollectionVectorStore(tech) for tech in SUPPORTED_TECH_COLLECTIONS
        }

    def get_store_for_tech(self, tech_or_lang: str) -> MultiCollectionVectorStore:
        cleaned = tech_or_lang.lower().replace(".", "").replace("-", "").replace(" ", "")
        if cleaned in self.stores:
            return self.stores[cleaned]
        for key in self.stores:
            if key in cleaned or cleaned in key:
                return self.stores[key]
        return self.stores["general_datasets"]

    def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any],
        tech_collection: Optional[str] = None,
    ) -> None:
        tech = tech_collection or metadata.get("framework") or metadata.get("language") or "general_datasets"
        store = self.get_store_for_tech(tech)
        vector = self.embedder.embed_query(text)
        store.upsert(
            ids=[doc_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata],
        )

    def search_across_tech(
        self,
        query: str,
        tech_filters: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        query_vec = self.embedder.embed_query(query)
        target_techs = tech_filters or list(self.stores.keys())
        all_results = []

        for tech in target_techs:
            store = self.get_store_for_tech(tech)
            matches = store.query(query_embedding=query_vec, top_k=top_k)
            all_results.extend(matches)

        # Sort combined results by distance (ascending = closest match)
        all_results.sort(key=lambda x: x.get("distance", 1.0))
        return all_results[:top_k]

    def get_statistics(self) -> Dict[str, Any]:
        stats = {}
        total_vectors = 0
        for name, store in self.stores.items():
            count = store.count()
            stats[name] = count
            total_vectors += count
        return {
            "total_collections": len(self.stores),
            "total_embeddings": total_vectors,
            "collections": stats,
            "embedding_model": self.embedder.model_name,
        }
