"""
Dataset Updater: Checks Hugging Face for new dataset versions weekly, downloads updates,
and performs incremental indexing (rebuilding only changed/new files).
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.services.datasets.dataset_downloader import DatasetDownloader, SUPPORTED_DATASETS
from app.services.datasets.dataset_indexer import DatasetIndexer
try:
    from vector_db.vector_db_manager import VectorDBManager
except ImportError:
    from backend.vector_db.vector_db_manager import VectorDBManager


logger = logging.getLogger(__name__)


class DatasetUpdater:
    def __init__(self, vector_db: VectorDBManager, base_dir: str = "data/datasets") -> None:
        self.vector_db = vector_db
        self.downloader = DatasetDownloader(base_dir=base_dir)
        self.indexer = DatasetIndexer(vector_db=vector_db)
        self.base_dir = Path(base_dir)

    def check_and_update_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Checks all supported Hugging Face datasets. If updated or missing, downloads and incrementally re-indexes.
        """
        results = {}
        for dname in SUPPORTED_DATASETS:
            res = self.update_dataset(dname, force=force)
            results[dname] = res

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "datasets_updated": results,
        }

    def update_dataset(self, dataset_name: str, force: bool = False) -> Dict[str, Any]:
        ddir = self.downloader.get_dataset_dir(dataset_name)
        meta_file = ddir / "metadata.json"

        needs_indexing = False
        old_version = "none"

        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    old_meta = json.load(f)
                    old_version = old_meta.get("version", "1.0.0")
            except Exception:
                pass

        if not self.downloader.is_downloaded(dataset_name) or force:
            logger.info("Downloading/Updating dataset %s...", dataset_name)
            meta = self.downloader.download_dataset(dataset_name, force_redownload=force)
            needs_indexing = True
        else:
            meta = json.load(open(meta_file, "r", encoding="utf-8"))

        index_stats = {}
        if needs_indexing:
            logger.info("Incremental indexing for changed dataset %s...", dataset_name)
            index_stats = self.indexer.index_dataset(dataset_name, base_dir=str(self.base_dir))
            meta["last_indexed_at"] = datetime.now(timezone.utc).isoformat()
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

        return {
            "dataset_name": dataset_name,
            "previous_version": old_version,
            "current_version": meta.get("version", "1.0.0"),
            "status": "updated" if needs_indexing else "up_to_date",
            "index_stats": index_stats,
        }
