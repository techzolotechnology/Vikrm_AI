"""
Reranker: Scores and reranks retrieved context candidates for relevance, code density, and tag alignment.
"""
import re
from typing import Any, Dict, List


class ContextReranker:
    def __init__(self) -> None:
        pass

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        query_terms = set(re.findall(r"\w+", query.lower()))

        scored_candidates = []
        for cand in candidates:
            doc_text = cand.get("document", "")
            meta = cand.get("metadata", {})

            # Base distance score (Chroma distance: lower is better)
            distance = cand.get("distance", 1.0)
            base_score = max(0.0, 1.0 - (distance / 2.0))

            # Keyword overlap boost
            doc_terms = set(re.findall(r"\w+", doc_text.lower()))
            overlap = len(query_terms.intersection(doc_terms))
            overlap_score = (overlap / max(1, len(query_terms))) * 0.3

            # Code block boost
            code_boost = 0.2 if ("```" in doc_text or "def " in doc_text or "function" in doc_text or "import " in doc_text) else 0.0

            # Title match boost
            title = meta.get("title", "").lower()
            title_boost = 0.25 if any(t in title for t in query_terms) else 0.0

            final_score = base_score + overlap_score + code_boost + title_boost

            cand_copy = dict(cand)
            cand_copy["rerank_score"] = round(final_score, 4)
            scored_candidates.append(cand_copy)

        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]
