"""
Script to initialize and index all datasets and framework docs into Vector DB.
"""
import sys
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO)

from app.services.datasets.dataset_downloader import SUPPORTED_DATASETS
from app.services.datasets.dataset_manager import DatasetManager

def main():
    manager = DatasetManager()
    print(f"Total Configured Datasets: {len(SUPPORTED_DATASETS)}")
    
    for name in SUPPORTED_DATASETS:
        print(f"Indexing {name}...")
        res = manager.download_and_index(name, force=True)
        print(f"  Indexed {name}: {res.get('index_stats')}")
        
    print("\nFinal Vector DB Statistics:", manager.vector_db.get_statistics())

if __name__ == "__main__":
    main()
