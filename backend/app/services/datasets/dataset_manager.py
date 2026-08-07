"""
Dataset Manager: Core service orchestrating downloading, cleaning, indexing, local caching,
and version tracking across all Hugging Face datasets.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.datasets.dataset_cleaner import DatasetCleaner
from app.services.datasets.dataset_downloader import DatasetDownloader, SUPPORTED_DATASETS
from app.services.datasets.dataset_indexer import DatasetIndexer
from app.services.datasets.dataset_updater import DatasetUpdater
try:
    from vector_db.vector_db_manager import VectorDBManager
except ImportError:
    from backend.vector_db.vector_db_manager import VectorDBManager


logger = logging.getLogger(__name__)


class DatasetManager:
    def __init__(self, base_dir: str = "data/datasets", vector_db: Optional[VectorDBManager] = None) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db = vector_db or VectorDBManager()
        self.downloader = DatasetDownloader(base_dir=str(self.base_dir))
        self.cleaner = DatasetCleaner()
        self.indexer = DatasetIndexer(vector_db=self.vector_db)
        self.updater = DatasetUpdater(vector_db=self.vector_db, base_dir=str(self.base_dir))

    def list_datasets(self) -> List[Dict[str, Any]]:
        datasets = []
        for name in SUPPORTED_DATASETS:
            ddir = self.base_dir / name
            meta_file = ddir / "metadata.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["installed"] = True
                        datasets.append(meta)
                        continue
                except Exception:
                    pass

            config = SUPPORTED_DATASETS[name]
            datasets.append({
                "dataset_name": name,
                "hf_path": config["hf_path"],
                "description": config["description"],
                "language": config["language"],
                "framework": config["framework"],
                "installed": False,
                "document_count": 0,
                "size_bytes": 0,
                "version": "1.0.0",
            })
        return datasets

    def download_and_index(self, dataset_name: str, force: bool = False) -> Dict[str, Any]:
        meta = self.downloader.download_dataset(dataset_name, force_redownload=force)
        index_res = self.indexer.index_dataset(dataset_name, base_dir=str(self.base_dir))
        meta["index_stats"] = index_res
        return meta

    def update_all(self, force: bool = False) -> Dict[str, Any]:
        return self.updater.check_and_update_all(force=force)

    def reindex_dataset(self, dataset_name: str) -> Dict[str, Any]:
        return self.indexer.index_dataset(dataset_name, base_dir=str(self.base_dir))

    def delete_dataset(self, dataset_name: str) -> Dict[str, Any]:
        ddir = self.base_dir / dataset_name
        deleted_bytes = 0
        if ddir.exists():
            import shutil
            for f in ddir.glob("**/*"):
                if f.is_file():
                    deleted_bytes += f.stat().st_size
            shutil.rmtree(ddir)

        # Clear vector database entries for dataset
        for store in self.vector_db.stores.values():
            store.delete_where({"dataset": dataset_name})

        return {
            "dataset_name": dataset_name,
            "status": "deleted",
            "reclaimed_bytes": deleted_bytes,
        }

    def ensure_datasets_for_tech(self, prompt_or_tech: str) -> List[str]:
        """
        Automatically detects tech stack in prompt, downloads and indexes missing datasets locally.
        Offline-first: skips if already present locally.
        """
        text = prompt_or_tech.lower()
        required_datasets = []

        # Tech to dataset mappings
        if any(w in text for w in ["python", "fastapi", "django", "flask", "ai", "pandas", "numpy"]):
            required_datasets.extend(["code_search_net", "CodeAlpaca_20K"])

        if any(w in text for w in ["react", "typescript", "javascript", "vue", "next", "node", "frontend"]):
            required_datasets.extend(["CommitPack", "SWE_bench"])

        if any(w in text for w in ["algorithm", "sort", "binary", "tree", "problem", "leetcode"]):
            required_datasets.extend(["codeparrot_apps", "MBPP", "openai_humaneval"])

        if not required_datasets:
            required_datasets = ["code_search_net", "CodeAlpaca_20K"]

        synced = []
        for name in set(required_datasets):
            if name in SUPPORTED_DATASETS:
                meta_file = self.base_dir / name / "metadata.json"
                if not meta_file.exists():
                    logger.info("[Automatic Knowledge System] Auto-downloading missing dataset: %s", name)
                    try:
                        self.download_and_index(name)
                        synced.append(name)
                    except Exception as exc:
                        logger.warning("[Automatic Knowledge System] Failed downloading dataset %s: %s", name, exc)
                else:
                    synced.append(name)
        return synced

