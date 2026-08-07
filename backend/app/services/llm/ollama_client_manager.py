"""
Ollama persistent HTTP Client Manager & Connection Pool.

Provides a self-healing, singleton HTTP client pool with connection keep-alive,
pre-flight health checks, IPv4 preference on Windows, auto-spawning process recovery,
and pool auto-recreation on socket failure.
"""
import asyncio
import sys
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.ollama_process_manager import OllamaProcessManager

logger = get_logger(__name__)


def get_normalized_ollama_urls(base_url: Optional[str] = None) -> List[str]:
    """
    Returns candidate Ollama endpoints.
    When a custom base_url is passed, probe only that target URL.
    """
    configured = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
    candidates = [configured]
    
    if "localhost" in configured:
        candidates.append(configured.replace("localhost", "127.0.0.1"))

    # Only include default 11434 fallbacks when base_url is omitted or uses 11434
    if base_url is None or "11434" in configured:
        candidates.append("http://127.0.0.1:11434")
        candidates.append("http://localhost:11434")
    
    # Deduplicate preserving order
    return list(dict.fromkeys(candidates))


class OllamaClientManager:
    """
    Singleton HTTP client pool manager for Ollama connection management.
    """
    _instance: Optional["OllamaClientManager"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._active_base_url: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "OllamaClientManager":
        if cls._instance is None:
            cls._instance = OllamaClientManager()
        return cls._instance

    async def get_client(self, force_recreate: bool = False) -> httpx.AsyncClient:
        """
        Returns a persistent shared AsyncClient instance.
        Recreates the client pool if requested or if closed.
        """
        async with self._lock:
            if force_recreate or self._client is None or self._client.is_closed:
                if self._client and not self._client.is_closed:
                    try:
                        await self._client.aclose()
                        logger.info("[Provider Destroyed] Closed old Ollama HTTP client pool")
                    except Exception as exc:
                        logger.warning("[Provider Destroyed] Notice closing old client pool: %s", exc)

                limits = httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=100,
                    keepalive_expiry=10.0
                )
                timeouts = httpx.Timeout(connect=5.0, read=300.0, write=120.0, pool=120.0)
                
                self._client = httpx.AsyncClient(
                    limits=limits,
                    timeout=timeouts,
                    headers={"Connection": "keep-alive"}
                )
                logger.info("[Provider Created] Initialized persistent Ollama HTTP client pool (max_conns=100, keepalive_expiry=10s)")
            return self._client

    async def ping_health(self, base_url: Optional[str] = None) -> Optional[str]:
        """
        Pre-flight health check pinging GET /api/tags across normalized target endpoints.
        Uses an isolated short-lived HTTP client to avoid pool pollution.
        If all endpoints fail, invokes OllamaProcessManager.ensure_ollama_running()
        to attempt auto-starting 'ollama serve'.
        Returns healthiest URL if responsive, else None.
        """
        urls = get_normalized_ollama_urls(base_url)

        async with httpx.AsyncClient(timeout=httpx.Timeout(2.5, connect=1.0)) as probe_client:
            for target_url in urls:
                endpoint = f"{target_url}/api/tags"
                logger.info("[Health Check] Pinging Ollama endpoint: %s", endpoint)
                try:
                    resp = await probe_client.get(endpoint)
                    if resp.status_code == 200:
                        self._active_base_url = target_url
                        logger.info("[Health Check] Endpoint %s responded HEALTHY", target_url)
                        return target_url
                    else:
                        logger.warning("[Health Check] Endpoint %s returned HTTP %s", target_url, resp.status_code)
                except Exception as exc:
                    logger.warning("[Health Check] Endpoint %s failed ping: %s", target_url, exc)
                    continue

        # All pings failed: Attempt process auto-launch recovery
        logger.warning("[Health Check] All Ollama endpoints unresponsive. Triggering OllamaProcessManager...")
        if await OllamaProcessManager.ensure_ollama_running():
            # Re-probe candidate endpoints after auto-launch
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.5, connect=1.0)) as probe_client:
                for target_url in urls:
                    try:
                        resp = await probe_client.get(f"{target_url}/api/tags")
                        if resp.status_code == 200:
                            self._active_base_url = target_url
                            logger.info("[Health Check Recovery] Endpoint %s healthy after process auto-launch", target_url)
                            return target_url
                    except Exception:
                        continue

        return None

    async def fetch_installed_models(self, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch installed models via GET /api/tags with fallback recovery."""
        target_url = await self.ping_health(base_url)
        if not target_url:
            return []
        
        try:
            client = await self.get_client()
            resp = await client.get(f"{target_url}/api/tags", timeout=httpx.Timeout(5.0))
            if resp.status_code == 200:
                return resp.json().get("models", [])
        except Exception as exc:
            logger.warning("[OllamaClientManager] Failed to parse models from %s: %s", target_url, exc)
        return []

    async def trigger_auto_pull(self, model: str, target_url: str) -> bool:
        """Trigger model auto-pull trigger on status 404."""
        try:
            client = await self.get_client()
            pull_endpoint = f"{target_url}/api/pull"
            logger.info("[Auto Recovery] Triggering auto-pull for missing model '%s' at %s", model, pull_endpoint)
            resp = await client.post(
                pull_endpoint,
                json={"name": model, "stream": False},
                timeout=httpx.Timeout(15.0)
            )
            if resp.status_code == 200:
                logger.info("[Auto Recovery] Model pull initiated successfully for '%s'", model)
                return True
        except Exception as exc:
            logger.warning("[Auto Recovery] Auto-pull trigger notice: %s", exc)
        return False

    async def close(self) -> None:
        """Gracefully shutdown client pool."""
        async with self._lock:
            if self._client and not self._client.is_closed:
                try:
                    await self._client.aclose()
                    logger.info("[Provider Destroyed] Ollama HTTP client pool shutdown complete.")
                except Exception as exc:
                    logger.warning("Notice shutting down Ollama HTTP client: %s", exc)
                finally:
                    self._client = None


ollama_client_manager = OllamaClientManager.get_instance()
