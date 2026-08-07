"""
Dataset Indexer: Reads cleaned dataset files and indexes chunked embeddings into ChromaDB vector stores.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from app.services.datasets.dataset_cleaner import DatasetCleaner
from app.services.embeddings.chunker import DocumentChunker
from app.services.embeddings.embedder import CodeEmbedder
from app.services.embeddings.vector_store import MultiCollectionVectorStore
try:
    from vector_db.vector_db_manager import VectorDBManager
except ImportError:
    from backend.vector_db.vector_db_manager import VectorDBManager


logger = logging.getLogger(__name__)


class DatasetIndexer:
    def __init__(self, vector_db: VectorDBManager) -> None:
        self.vector_db = vector_db
        self.cleaner = DatasetCleaner()
        self.chunker = DocumentChunker()
        self.embedder = self.vector_db.embedder

    def index_dataset(
        self,
        dataset_name: str,
        base_dir: str = "data/datasets",
        batch_size: int = 64,
    ) -> Dict[str, Any]:
        ddir = Path(base_dir) / dataset_name
        docs_file = ddir / "documents.jsonl"
        if not docs_file.exists():
            raise FileNotFoundError(f"Documents file missing for dataset {dataset_name} at {docs_file}")

        logger.info("Indexing dataset %s into vector storage...", dataset_name)
        raw_records = []
        with open(docs_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        raw_records.append(json.loads(line))
                    except Exception:
                        pass

        cleaned_records = self.cleaner.clean_batch(raw_records, dataset_name=dataset_name)
        indexed_chunks = 0

        ids_batch: List[str] = []
        docs_batch: List[str] = []
        metas_batch: List[Dict[str, Any]] = []

        for record_idx, rec in enumerate(cleaned_records):
            doc_meta = {
                "dataset": dataset_name,
                "language": rec.get("language", "text"),
                "framework": rec.get("framework", "general"),
                "title": rec.get("title", ""),
                "description": rec.get("description", ""),
                "difficulty": rec.get("difficulty", "intermediate"),
                "tags": ",".join(rec.get("tags", [])),
            }

            text_content = f"Title: {rec.get('title')}\nDescription: {rec.get('description')}\nLanguage: {rec.get('language')}\nCode:\n{rec.get('code')}"
            chunks = self.chunker.chunk_document(text_content, metadata=doc_meta)

            for chunk_item in chunks:
                chunk_id = f"{dataset_name}-{record_idx}-{chunk_item['metadata']['chunk_index']}"
                ids_batch.append(chunk_id)
                docs_batch.append(chunk_item["text"])
                metas_batch.append(chunk_item["metadata"])

                if len(ids_batch) >= batch_size:
                    self._flush_batch(ids_batch, docs_batch, metas_batch)
                    indexed_chunks += len(ids_batch)
                    ids_batch, docs_batch, metas_batch = [], [], []

        if ids_batch:
            self._flush_batch(ids_batch, docs_batch, metas_batch)
            indexed_chunks += len(ids_batch)

        logger.info("Dataset %s indexed successfully with %d total chunk embeddings.", dataset_name, indexed_chunks)
        return {
            "dataset_name": dataset_name,
            "raw_records": len(raw_records),
            "cleaned_records": len(cleaned_records),
            "indexed_chunks": indexed_chunks,
        }

    def _flush_batch(
        self,
        ids: List[str],
        docs: List[str],
        metas: List[Dict[str, Any]],
    ) -> None:
        vectors = self.embedder.embed_texts(docs)
        # Store in framework/language specific collection as well as general_datasets
        for i in range(len(ids)):
            tech = metas[i].get("framework") or metas[i].get("language") or "general_datasets"
            store = self.vector_db.get_store_for_tech(tech)
            store.upsert(
                ids=[ids[i]],
                embeddings=[vectors[i]],
                documents=[docs[i]],
                metadatas=[metas[i]],
            )
