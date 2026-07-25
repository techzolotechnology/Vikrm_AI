"""
Shared test fixtures.

Uses an in-memory SQLite DB for repository/service-level tests instead
of requiring a live MySQL instance — this keeps the suite fast and
runnable in CI/sandboxed environments while still exercising real SQL
execution (inserts, unique constraints, queries), not mocks. MySQL-
specific behavior (e.g. exact ENUM DDL) is covered separately by the
Alembic migration itself, which only runs against real MySQL.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401  ensures models are registered on Base.metadata
from app.core.database import Base


@pytest.fixture(autouse=True)
def isolated_vector_store(tmp_path, monkeypatch):
    """Every test gets its own ChromaDB directory and the deterministic
    (network-free) embedding provider, so memory/RAG tests never share
    state with each other or need a model download."""
    from app.core import vector_store
    from app.core.config import settings
    from app.services.embeddings import registry as embedding_registry

    monkeypatch.setattr(settings, "CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "deterministic")
    vector_store.get_chroma_client.cache_clear()
    embedding_registry._instance_cache.clear()
    yield
    vector_store.get_chroma_client.cache_clear()
    embedding_registry._instance_cache.clear()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


def _make_mock_ollama_app(*, fail: bool = False):
    import json

    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse

    app = FastAPI()

    @app.post("/api/chat")
    async def chat(request: dict):
        async def gen():
            words = ["Hello", " there", "!"]
            for i, word in enumerate(words):
                if fail and i == 1:
                    yield json.dumps({"error": "model crashed"}) + "\n"
                    return
                yield (
                    json.dumps({"message": {"role": "assistant", "content": word}, "done": False})
                    + "\n"
                )
            yield json.dumps({"message": {"role": "assistant", "content": ""}, "done": True}) + "\n"

        return StreamingResponse(gen(), media_type="application/x-ndjson")

    return app


@pytest_asyncio.fixture
async def mock_ollama_server():
    """Spins up a real ASGI server on a free local port that speaks
    Ollama's exact newline-delimited-JSON streaming protocol, so
    provider/service tests exercise real HTTP streaming rather than mocks."""
    import asyncio
    import socket

    import uvicorn

    def find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    port = find_free_port()
    app = _make_mock_ollama_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    for _ in range(50):
        if server.started:
            break
        await asyncio.sleep(0.05)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    await task
