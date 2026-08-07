"""
Unit and Integration Tests for Vikrm Retrieval-Augmented AI Software Engineering Pipeline.
Tests dataset downloads, cleaning, embedding generation, vector search, retriever, RAG chat pipeline,
and project templates.
"""
import json
import pytest
from pathlib import Path

from app.services.datasets.dataset_cleaner import DatasetCleaner
from app.services.datasets.dataset_downloader import DatasetDownloader
from app.services.datasets.dataset_manager import DatasetManager
from app.services.embeddings.embedder import CodeEmbedder
from app.services.embeddings.chunker import DocumentChunker
from app.services.rag.retriever import KnowledgeRetriever
from app.services.rag.context_builder import RAGContextBuilder
try:
    from project_templates.template_manager import ProjectTemplateLibrary
except ImportError:
    from backend.project_templates.template_manager import ProjectTemplateLibrary

try:
    from vector_db.vector_db_manager import VectorDBManager
except ImportError:
    from backend.vector_db.vector_db_manager import VectorDBManager



@pytest.fixture
def tmp_dataset_dir(tmp_path):
    dpath = tmp_path / "datasets"
    dpath.mkdir(parents=True, exist_ok=True)
    return str(dpath)


def test_dataset_cleaner():
    cleaner = DatasetCleaner()

    raw = {
        "title": "Test Python Function",
        "description": "Calculates factorial of a number.",
        "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)\n",
        "language": "python",
        "framework": "standard",
    }

    cleaned = cleaner.clean_record(raw, dataset_name="test_dataset")
    assert cleaned is not None
    assert cleaned["title"] == "Test Python Function"
    assert cleaned["language"] == "python"
    assert "factorial" in cleaned["code"]

    # Test deduplication
    dup = cleaner.clean_record(raw, dataset_name="test_dataset")
    assert dup is None


def test_dataset_downloader(tmp_dataset_dir):
    downloader = DatasetDownloader(base_dir=tmp_dataset_dir)
    meta = downloader.download_dataset("openai_humaneval")

    assert meta["dataset_name"] == "openai_humaneval"
    assert meta["document_count"] > 0
    assert downloader.is_downloaded("openai_humaneval")


def test_embedder():
    embedder = CodeEmbedder()
    vecs = embedder.embed_texts(["def hello(): print('world')", "import react from 'react'"])
    assert len(vecs) == 2
    assert len(vecs[0]) == embedder.dimension

    q_vec = embedder.embed_query("Build a React dashboard")
    assert len(q_vec) == embedder.dimension


def test_chunker():
    chunker = DocumentChunker(max_chunk_size=200, overlap=30)
    meta = {"title": "Sample Doc", "type": "code", "language": "python"}
    code_text = "class App:\n" + "\n".join([f"    def method_{i}(self):\n        pass" for i in range(20)])

    chunks = chunker.chunk_document(code_text, metadata=meta)
    assert len(chunks) >= 2
    assert "text" in chunks[0]
    assert chunks[0]["metadata"]["chunk_index"] == 0


def test_vector_db_manager(tmp_path):
    vdb = VectorDBManager()
    vdb.index_document(
        doc_id="test-react-1",
        text="export function Button() { return <button className='btn'>Click</button>; }",
        metadata={"framework": "react", "language": "typescript", "title": "React Button"},
        tech_collection="react",
    )

    stats = vdb.get_statistics()
    assert stats["total_collections"] > 0

    results = vdb.search_across_tech("React button component", tech_filters=["react"], top_k=3)
    assert len(results) >= 1
    assert "Button" in results[0]["document"]


def test_project_template_library():
    lib = ProjectTemplateLibrary()
    templates = lib.list_templates()
    assert len(templates) == 19


    react_t = lib.get_template("react")
    assert react_t is not None
    assert "package.json" in react_t["files"]
    assert "App.tsx" in react_t["structure"] or "src/App.tsx" in react_t["structure"]


def test_retriever_and_context_builder():
    retriever = KnowledgeRetriever()
    res = retriever.retrieve_context("Build a React Dashboard with FastAPI", top_k=5)

    assert "examples" in res
    assert "docs" in res
    assert "templates" in res
    assert len(res["templates"]) > 0

    builder = RAGContextBuilder()
    augmented = builder.build_augmented_prompt("Build a React Dashboard with FastAPI", res)
    assert "RECOMMENDED PROJECT TEMPLATES" in augmented
    assert "USER REQUEST: Build a React Dashboard with FastAPI" in augmented


def test_large_prompt_truncation():
    retriever = KnowledgeRetriever()
    res = retriever.retrieve_context("Build an ERP system with microservices", top_k=10)

    builder = RAGContextBuilder(max_context_chars=1000)
    augmented = builder.build_augmented_prompt("Build an ERP system", res)
    assert len(augmented) <= 2500  # Including section wrappers
