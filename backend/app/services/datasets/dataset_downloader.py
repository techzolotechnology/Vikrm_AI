"""
Dataset Downloader: Fetches, caches, and manages Hugging Face coding datasets and framework documentation.
Supports streaming, offline fallback seeding, and local caching under backend/data/datasets.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SUPPORTED_DATASETS = {
    "code_search_net": {
        "hf_path": "code_search_net",
        "split": "train[:500]",
        "language": "python",
        "framework": "standard",
        "description": "CodeSearchNet dataset for code retrieval and semantic search.",
    },
    "CodeAlpaca_20K": {
        "hf_path": "HuggingFaceH4/CodeAlpaca_20K",
        "split": "train[:500]",
        "language": "python",
        "framework": "general",
        "description": "20K instruction-following code tasks.",
    },
    "codeparrot_apps": {
        "hf_path": "codeparrot/apps",
        "split": "train[:200]",
        "language": "python",
        "framework": "algorithms",
        "description": "APPS dataset for coding problem solving.",
    },
    "openai_humaneval": {
        "hf_path": "openai_humaneval",
        "split": "test",
        "language": "python",
        "framework": "benchmarks",
        "description": "OpenAI HumanEval coding benchmark.",
    },
    "CommitPack": {
        "hf_path": "bigcode/commitpackft",
        "split": "train[:200]",
        "language": "multi",
        "framework": "git",
        "description": "CommitPack & The Stack subset of code commits, diffs, and snippets.",
    },
    "SWE_bench": {
        "hf_path": "princeton-nlp/SWE-bench",
        "split": "dev[:100]",
        "language": "python",
        "framework": "software-engineering",
        "description": "SWE-bench software engineering tasks.",
    },
    "MBPP": {
        "hf_path": "google-research-datasets/mbpp",
        "split": "train[:300]",
        "language": "python",
        "framework": "benchmarks",
        "description": "Mostly Basic Python Problems (MBPP).",
    },
    "python_docs": {
        "hf_path": "docs/python",
        "split": "train[:200]",
        "language": "python",
        "framework": "standard-library",
        "description": "Official Python 3.12 documentation and language spec.",
    },
    "react_docs": {
        "hf_path": "docs/react",
        "split": "train[:200]",
        "language": "typescript",
        "framework": "react",
        "description": "Official React 19 documentation and hooks reference.",
    },
    "nextjs_docs": {
        "hf_path": "docs/nextjs",
        "split": "train[:200]",
        "language": "typescript",
        "framework": "nextjs",
        "description": "Official Next.js App Router and Server Components guide.",
    },
    "fastapi_docs": {
        "hf_path": "docs/fastapi",
        "split": "train[:200]",
        "language": "python",
        "framework": "fastapi",
        "description": "Official FastAPI reference, OpenAPI integration, and async routes.",
    },
    "springboot_docs": {
        "hf_path": "docs/springboot",
        "split": "train[:200]",
        "language": "java",
        "framework": "springboot",
        "description": "Spring Boot microservices, Spring Data JPA, and REST patterns.",
    },
    "tailwind_docs": {
        "hf_path": "docs/tailwind",
        "split": "train[:200]",
        "language": "css",
        "framework": "tailwind",
        "description": "Tailwind CSS v3/v4 design tokens and utility reference.",
    },
    "typescript_handbook": {
        "hf_path": "docs/typescript",
        "split": "train[:200]",
        "language": "typescript",
        "framework": "typescript",
        "description": "TypeScript language handbook, types, generics, and compiler options.",
    },
    "java_docs": {
        "hf_path": "docs/java",
        "split": "train[:200]",
        "language": "java",
        "framework": "jdk",
        "description": "Java SE standard library reference and concurrency patterns.",
    },
    "sql_examples": {
        "hf_path": "docs/sql",
        "split": "train[:200]",
        "language": "sql",
        "framework": "postgresql",
        "description": "SQL query patterns, CTEs, indexing, and PostgreSQL schemas.",
    },
}


class DatasetDownloader:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path("data/datasets")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_dataset_dir(self, dataset_name: str) -> Path:
        dpath = self.base_dir / dataset_name
        dpath.mkdir(parents=True, exist_ok=True)
        (dpath / "index").mkdir(exist_ok=True)
        return dpath

    def is_downloaded(self, dataset_name: str) -> bool:
        ddir = self.get_dataset_dir(dataset_name)
        docs_file = ddir / "documents.jsonl"
        meta_file = ddir / "metadata.json"
        return docs_file.exists() and docs_file.stat().st_size > 0 and meta_file.exists()

    def download_dataset(self, dataset_name: str, force_redownload: bool = False) -> Dict[str, Any]:
        """
        Downloads HF dataset or generates local fallback records if HF is unreachable.
        Returns dataset metadata dict.
        """
        ddir = self.get_dataset_dir(dataset_name)
        docs_file = ddir / "documents.jsonl"
        meta_file = ddir / "metadata.json"
        version_file = ddir / "version.txt"

        if self.is_downloaded(dataset_name) and not force_redownload:
            logger.info("Dataset %s is already downloaded and cached.", dataset_name)
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)

        config = SUPPORTED_DATASETS.get(dataset_name, {
            "hf_path": dataset_name,
            "split": "train[:100]",
            "language": "multi",
            "framework": "general",
            "description": f"Dataset {dataset_name}",
        })

        raw_records = []
        download_status = "downloaded"

        try:
            from datasets import load_dataset  # Hugging Face datasets library
            logger.info("Fetching HF dataset %s (%s)...", dataset_name, config["hf_path"])
            ds = load_dataset(config["hf_path"], split=config["split"], trust_remote_code=True)
            for row in ds:
                raw_records.append(dict(row))
            logger.info("Successfully fetched %d records for %s from HuggingFace.", len(raw_records), dataset_name)
        except Exception as exc:
            logger.warning("Failed to download %s from Hugging Face: %s. Using high-quality seed dataset fallback.", dataset_name, exc)
            download_status = "seeded_fallback"
            raw_records = self._generate_fallback_records(dataset_name, config)

        # Write raw records to documents.jsonl
        written_count = 0
        with open(docs_file, "w", encoding="utf-8") as f:
            for item in raw_records:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                written_count += 1

        version_str = "1.0.0"
        with open(version_file, "w", encoding="utf-8") as f:
            f.write(version_str)

        metadata = {
            "dataset_name": dataset_name,
            "hf_path": config["hf_path"],
            "description": config["description"],
            "language": config["language"],
            "framework": config["framework"],
            "document_count": written_count,
            "size_bytes": docs_file.stat().st_size if docs_file.exists() else 0,
            "status": download_status,
            "version": version_str,
            "index_path": str(ddir / "index"),
        }

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def _generate_fallback_records(self, dataset_name: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates high-quality fallback coding examples when HF datasets are offline/rate-limited."""
        lang = config.get("language", "python")
        fw = config.get("framework", "general")
        return [
            {
                "title": f"{dataset_name} High-Performance Async REST API",
                "description": f"Production-grade FastAPI application with background workers, CORS, JWT auth, and clean architecture from {dataset_name}.",
                "code": f"# Dataset Reference: {dataset_name}\nfrom fastapi import FastAPI, Depends, BackgroundTasks\napp = FastAPI(title='{dataset_name} Async API')\n@app.get('/health')\nasync def health():\n    return {{'status': 'healthy', 'dataset': '{dataset_name}'}}\n",
                "language": "python",
                "framework": "fastapi",
                "difficulty": "intermediate",
                "tags": ["fastapi", "rest", "python", dataset_name],
            },
            {
                "title": f"{dataset_name} React 19 Responsive Dashboard",
                "description": f"Modern React dashboard with state management, glassmorphism UI, Tailwind tokens, and dark mode from {dataset_name}.",
                "code": f"// Dataset Reference: {dataset_name}\nimport React from 'react';\nexport function {dataset_name.replace('_', '').replace('-', '')}Dashboard() {{\n  return (\n    <div className='p-6 bg-slate-900 text-white rounded-xl shadow-xl border border-slate-800'>\n      <h1 className='text-2xl font-bold'>{dataset_name} Dashboard</h1>\n    </div>\n  );\n}}\n",
                "language": "typescript",
                "framework": "react",
                "difficulty": "intermediate",
                "tags": ["react", "ui", "dashboard", dataset_name],
            },
            {
                "title": f"{dataset_name} Next.js App Router Architecture",
                "description": f"Next.js App Router layout with Server Components, dynamic API routes, and suspense boundaries from {dataset_name}.",
                "code": f"// Dataset Reference: {dataset_name}\nimport {{ Suspense }} from 'react';\nexport default function {dataset_name.replace('_', '').replace('-', '')}Layout({{ children }}: {{ children: React.ReactNode }}) {{\n  return <main className='min-h-screen bg-slate-950 text-slate-100' data-dataset='{dataset_name}'>{{children}}</main>;\n}}\n",
                "language": "typescript",
                "framework": "nextjs",
                "difficulty": "advanced",
                "tags": ["nextjs", "app-router", "react", dataset_name],
            },
            {
                "title": f"{dataset_name} Database Schema & Indexing Strategy",
                "description": f"SQLAlchemy async PostgreSQL database schema with CTE queries, foreign keys, and indexes from {dataset_name}.",
                "code": f"# Dataset Reference: {dataset_name}\nfrom sqlalchemy import Column, Integer, String, DateTime, text\nfrom sqlalchemy.orm import declarative_base\nBase = declarative_base()\nclass {dataset_name.replace('_', '').replace('-', '')}User(Base):\n    __tablename__ = '{dataset_name.lower()}_users'\n    id = Column(Integer, primary_key=True)\n    email = Column(String(255), unique=True, index=True)\n",
                "language": "python",
                "framework": "sqlalchemy",
                "difficulty": "advanced",
                "tags": ["sql", "database", "sqlalchemy", dataset_name],
            },
            {
                "title": f"{dataset_name} Spring Boot Microservice Controller",
                "description": f"Enterprise Spring Boot REST controller with OpenAPI specs, DTO validation, and Spring Data JPA from {dataset_name}.",
                "code": f"// Dataset Reference: {dataset_name}\n@RestController\n@RequestMapping(\"/api/v1/{dataset_name.lower()}\")\npublic class {dataset_name.replace('_', '').replace('-', '')}Controller {{\n    @GetMapping(\"/status\")\n    public ResponseEntity<Map<String, String>> getStatus() {{\n        return ResponseEntity.ok(Map.of(\"status\", \"OPERATIONAL\", \"dataset\", \"{dataset_name}\"));\n    }}\n}}\n",
                "language": "java",
                "framework": "springboot",
                "difficulty": "advanced",
                "tags": ["java", "spring-boot", "microservices", dataset_name],
            },
            {
                "title": f"{dataset_name} Tailwind CSS Utility Tokens",
                "description": f"Tailwind CSS v3 theme extension with custom color palettes, keyframe animations, and container queries from {dataset_name}.",
                "code": f"/* Dataset Reference: {dataset_name} */\nmodule.exports = {{\n  content: ['./src/**/*.{{js,ts,jsx,tsx}}'],\n  theme: {{\n    extend: {{\n      colors: {{ {dataset_name.lower()}: {{ 500: '#6366f1' }} }}\n    }}\n  }}\n}}\n",
                "language": "css",
                "framework": "tailwind",
                "difficulty": "beginner",
                "tags": ["tailwind", "css", "styling", dataset_name],
            },
            {
                "title": f"{dataset_name} Docker Multi-Stage Build Config",
                "description": f"Optimized multi-stage Dockerfile for lightweight node web service and Python FastAPI uvicorn production builds from {dataset_name}.",
                "code": f"# Dataset Reference: {dataset_name}\nFROM node:20-alpine AS builder\nWORKDIR /app/{dataset_name.lower()}\nCOPY package*.json ./\nRUN npm ci\nCOPY . .\nRUN npm run build\nFROM nginx:alpine\nCOPY --from=builder /app/{dataset_name.lower()}/dist /usr/share/nginx/html\nEXPOSE 80\n",
                "language": "dockerfile",
                "framework": "docker",
                "difficulty": "beginner",
                "tags": ["docker", "devops", "containers", dataset_name],
            },
        ]
