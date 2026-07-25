"""
Centralized application configuration.

All environment-driven settings live here as a single typed object.
No module in the codebase should call os.getenv directly — import
`settings` from this module instead. This is what lets us change
config sources (env file, vault, k8s secrets) later without touching
business logic.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "Vikrm"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- CORS ---
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        defaults = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        origins: List[str] = []
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    origins = json.loads(v)
                except Exception:
                    origins = [i.strip() for i in v.strip("[]").split(",") if i.strip()]
            else:
                origins = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = v

        # Combine defaults and env origins cleanly without duplicates
        combined = list(dict.fromkeys(defaults + [o.strip('"\' ') for o in origins]))
        return combined


    # --- Database (MySQL) ---
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "vikrm"
    MYSQL_PASSWORD: str = "vikrm_password"
    MYSQL_DATABASE: str = "vikrm"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def SQLALCHEMY_SYNC_DATABASE_URI(self) -> str:
        """Sync URI used by Alembic (which does not run inside the async loop)."""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    # --- Redis ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # --- Security (used from Milestone 2 onward, defined now so .env shape is stable) ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # --- LLM Providers ---
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    DEFAULT_LLM_PROVIDER: str = "ollama"
    DEFAULT_LLM_MODEL: str = "llama3.2"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""

    # --- Vector store / embeddings (Milestone 5: Memory, Milestone 6: RAG) ---
    CHROMA_PERSIST_DIR: str = "/app/data/chroma"
    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    MEMORY_SEARCH_TOP_K: int = 3

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Rate limiting (Milestone 13) ---
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120

    def validate_production_safety(self) -> None:
        """Refuses to boot in production with the default JWT secret —
        a real, common misconfiguration this check exists specifically
        to catch before it becomes a live vulnerability, not a
        theoretical concern."""
        if self.ENVIRONMENT == "production" and self.JWT_SECRET_KEY == "change-me-in-production":
            raise RuntimeError(
                "Refusing to start: JWT_SECRET_KEY is still the default value while "
                "ENVIRONMENT=production. Set a real secret (e.g. `openssl rand -hex 32`) "
                "in your environment before deploying."
            )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — Settings() parses env vars once per process."""
    return Settings()


settings = get_settings()
