"""
Retriever Engine: Hybrid multi-source retriever fetching code examples, official documentation,
and project templates based on user query intent.
"""
import logging
from typing import Any, Dict, List, Optional

try:
    from project_templates.template_manager import ProjectTemplateLibrary
except ImportError:
    from backend.project_templates.template_manager import ProjectTemplateLibrary

from app.services.rag.doc_indexer import DocumentationIndexer
from app.services.rag.reranker import ContextReranker
try:
    from vector_db.vector_db_manager import VectorDBManager
except ImportError:
    from backend.vector_db.vector_db_manager import VectorDBManager


logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    def __init__(self, vector_db: Optional[VectorDBManager] = None) -> None:
        self.vector_db = vector_db or VectorDBManager()
        self.reranker = ContextReranker()
        self.template_lib = ProjectTemplateLibrary()
        self.doc_indexer = DocumentationIndexer(vector_db=self.vector_db)
        # Seed official docs on startup
        try:
            self.doc_indexer.index_official_docs()
        except Exception as exc:
            logger.warning("Failed to auto-seed docs on startup: %s", exc)

    def retrieve_context(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Executes hybrid retrieval across:
        1. Code dataset examples (ChromaDB)
        2. Official documentation (ChromaDB)
        3. Matching Project Templates (Template Library + ChromaDB)
        """
        if not query or not query.strip():
            return {"examples": [], "docs": [], "templates": []}

        # 0. Automatic Knowledge System: Ensure required tech datasets exist locally
        try:
            from app.services.datasets.dataset_manager import DatasetManager
            dm = DatasetManager(vector_db=self.vector_db)
            dm.ensure_datasets_for_tech(query)
        except Exception as exc:
            logger.warning("[Automatic Knowledge System] Non-fatal auto-dataset sync warning: %s", exc)

        # 1. Multi-collection vector search
        raw_candidates = self.vector_db.search_across_tech(query, top_k=top_k * 2)

        # 2. Rerank code dataset candidates
        reranked_examples = self.reranker.rerank(query, raw_candidates, top_k=top_k)

        # 3. Retrieve relevant official documentation
        docs_store = self.vector_db.get_store_for_tech("docs")
        query_vec = self.vector_db.embedder.embed_query(query)
        doc_matches = docs_store.query(query_embedding=query_vec, top_k=5)
        reranked_docs = self.reranker.rerank(query, doc_matches, top_k=5)

        # 4. Retrieve top matching project templates
        matching_templates = self._match_project_templates(query)

        return {
            "query": query,
            "examples": reranked_examples,
            "docs": reranked_docs,
            "templates": matching_templates,
        }

    def _match_project_templates(self, query: str) -> List[Dict[str, Any]]:
        q_lower = query.lower()
        all_templates = self.template_lib.list_templates()
        matched = []

        for t in all_templates:
            key = t["key"].lower()
            title = t["title"].lower()
            fw = t["framework"].lower()
            desc = t["description"].lower()

            if key in q_lower or fw in q_lower or any(word in q_lower for word in title.split() if len(word) > 3):
                full_t = self.template_lib.get_template(key)
                if full_t:
                    matched.append(full_t)

        if not matched and "build" in q_lower:
            # Fallback to react or fastapi template if general build prompt
            matched.append(self.template_lib.get_template("react") or all_templates[0])

        return matched[:3]
