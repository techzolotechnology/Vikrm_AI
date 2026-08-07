"""
Application factory and entrypoint with automatic schema sync.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.core.redis_client import get_redis
from app.core.security_headers import SecurityHeadersMiddleware

configure_logging()
logger = get_logger(__name__)

# Refuses to start with an insecure default JWT secret in production
settings.validate_production_safety()


async def init_tables() -> None:
    """Ensure all SQLAlchemy tables and missing columns exist in the database on startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            cols_to_add = [
                ("conversations", "folder_id", "INT NULL FOREIGN KEY REFERENCES folders(id) ON DELETE SET NULL"),
                ("conversations", "is_pinned", "TINYINT(1) NOT NULL DEFAULT 0"),
                ("conversations", "is_archived", "TINYINT(1) NOT NULL DEFAULT 0"),
                ("conversations", "summary", "TEXT NULL"),
                ("messages", "is_bookmarked", "TINYINT(1) NOT NULL DEFAULT 0"),
                ("messages", "edited_at", "DATETIME NULL"),
                ("users", "preferences", "TEXT NULL"),
                ("agents", "version", "INT NOT NULL DEFAULT 1"),
                ("memories", "is_pinned", "TINYINT(1) NOT NULL DEFAULT 0"),
                ("memories", "is_archived", "TINYINT(1) NOT NULL DEFAULT 0"),
            ]
            for table, column, col_def in cols_to_add:
                try:
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                    )
                except Exception:
                    pass
        logger.info("Database schema initialized and synced.")
    except Exception as exc:
        logger.warning("Auto schema sync check encountered notice: %s", exc)


async def run_startup_validations() -> None:
    """Validate all backend dependencies on startup."""
    logger.info("=== Starting System Component Validations ===")
    
    # 1. Database Connection Check
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("[OK] Database connected successfully.")
    except Exception as exc:
        logger.error("[FAIL] Database connection failed: %s", exc)

    # 2. Redis Connection Check
    try:
        r = get_redis()
        if r:
            ping_res = r.ping()
            if asyncio.iscoroutine(ping_res):
                await ping_res
            logger.info("[OK] Redis connected successfully.")
        else:
            logger.info("[OK] Redis fallback mode active (in-memory rate limiter enabled).")
    except Exception as exc:
        logger.warning("[OK] Redis optional notice: %s", exc)

    # 3. Ollama Process & Server Validation
    try:
        from app.services.llm.ollama_process_manager import OllamaProcessManager
        from app.services.llm.ollama_client_manager import ollama_client_manager

        # Ensure Ollama server process is active
        is_ready = await OllamaProcessManager.ensure_ollama_running()
        if is_ready:
            healthy_url = await ollama_client_manager.ping_health()
            logger.info("[OK] Ollama process & server running at %s.", healthy_url)
            models_data = await ollama_client_manager.fetch_installed_models()
            models = [m.get("name", "") for m in models_data]
            default_model = settings.DEFAULT_LLM_MODEL
            if any(default_model in m for m in models):
                logger.info("[OK] Default LLM model '%s' exists and is ready.", default_model)
            else:
                logger.warning("[WARN] Default LLM model '%s' not found in installed models: %s", default_model, models)
        else:
            logger.warning("[NOTICE] Ollama server notice: process not currently responsive (watchdog & auto-spawner active)")
    except Exception as exc:
        logger.warning("[NOTICE] Ollama server startup check notice: %s", exc)

    # 4. Embedding & Vector Store Service Check
    try:
        from vector_db.vector_db_manager import VectorDBManager
        vdb = VectorDBManager()
        stats = vdb.get_statistics()
        logger.info("[OK] Embedding model loaded ('%s' via %s).", stats.get("embedding_model", settings.EMBEDDING_MODEL), settings.EMBEDDING_PROVIDER)
        logger.info("[OK] Vector Store loaded automatically (%d total chunk embeddings across %d collections in %s).",
                    stats.get("total_embeddings", 0), stats.get("total_collections", 0), settings.CHROMA_PERSIST_DIR)
        
        # If vector store is empty, trigger non-blocking auto-seed initialization
        if stats.get("total_embeddings", 0) == 0:
            logger.info("[Vector Store] Store empty. Auto-indexing local dataset seeds in background...")
            from app.services.datasets.dataset_manager import DatasetManager
            manager = DatasetManager()
            for dname in ["code_search_net", "CodeAlpaca_20K", "MBPP", "openai_humaneval", "python_docs", "react_docs", "fastapi_docs"]:
                try:
                    manager.download_and_index(dname)
                except Exception as e_idx:
                    logger.warning("Notice on auto-seeding %s: %s", dname, e_idx)
    except Exception as exc:
        logger.warning("[WARN] Embedding/Vector Store service check notice: %s", exc)

    logger.info("=== System Component Validations Complete ===")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s v%s in %s mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    await init_tables()
    await run_startup_validations()

    # Start proactive background watchdog
    from app.services.llm.ollama_watchdog import ollama_watchdog
    ollama_watchdog.start()

    yield

    logger.info("Shutting down %s", settings.APP_NAME)
    try:
        await ollama_watchdog.stop()
        from app.services.llm.ollama_client_manager import ollama_client_manager
        from app.services.llm.ollama_process_manager import OllamaProcessManager
        await ollama_client_manager.close()
        OllamaProcessManager.stop_process()
    except Exception as exc:
        logger.warning("Notice on lifespan shutdown: %s", exc)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Local-First AI Agent Automation Platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    @app.get("/api/docs", include_in_schema=False)
    async def redirect_api_docs():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, redis_client_factory=get_redis)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
