"""
Ollama Process Manager.

Provides native Windows / cross-platform process verification, auto-launching
of 'ollama serve' subprocesses, and health polling until HTTP 200 is confirmed.
"""
import asyncio
import os
import subprocess
import sys
import time
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaProcessManager:
    """
    Manages detection and auto-spawning of the Ollama server process.
    """

    _process: Optional[subprocess.Popen] = None
    _lock = asyncio.Lock()

    @classmethod
    async def is_ollama_responsive(cls, base_url: Optional[str] = None) -> bool:
        """
        Fast non-blocking probe to GET /api/tags via direct IPv4.
        """
        target_url = (base_url or settings.OLLAMA_BASE_URL).replace("localhost", "127.0.0.1").rstrip("/")
        endpoint = f"{target_url}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=1.0)) as client:
                resp = await client.get(endpoint)
                return resp.status_code == 200
        except Exception:
            return False

    @classmethod
    async def ensure_ollama_running(cls, max_wait_seconds: float = 15.0) -> bool:
        """
        Verifies that Ollama server is active.
        If unreachable, automatically spawns 'ollama serve' as a background subprocess
        and polls until GET /api/tags returns HTTP 200.
        """
        async with cls._lock:
            # 1. First probe check
            if await cls.is_ollama_responsive():
                logger.info("[Process Manager] Ollama server is running and responsive.")
                return True

            logger.warning("[Process Manager] Ollama server unresponsive. Attempting process auto-launch...")

            # 2. Spawn 'ollama serve'
            try:
                creation_flags = 0
                if sys.platform == "win32":
                    # CREATE_NO_WINDOW to run silently without spawning a console window
                    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

                cls._process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags,
                )
                logger.info("[Process Manager] Launched 'ollama serve' (PID: %d)", cls._process.pid)
            except FileNotFoundError:
                logger.error("[Process Manager] 'ollama' executable not found in system PATH. Install Ollama from https://ollama.com.")
                return False
            except Exception as exc:
                logger.error("[Process Manager] Failed launching 'ollama serve': %s", exc)
                return False

            # 3. Poll until ready
            start_time = time.perf_counter()
            while time.perf_counter() - start_time < max_wait_seconds:
                await asyncio.sleep(0.5)
                if await cls.is_ollama_responsive():
                    elapsed = time.perf_counter() - start_time
                    logger.info("[Process Manager] Ollama server successfully started & confirmed healthy in %.2fs.", elapsed)
                    return True

            logger.error("[Process Manager] Timed out waiting for Ollama server after %.1fs", max_wait_seconds)
            return False

    @classmethod
    def stop_process(cls) -> None:
        """Terminate managed process on application shutdown if spawned by manager."""
        if cls._process and cls._process.poll() is None:
            try:
                logger.info("[Process Manager] Terminating managed Ollama subprocess (PID: %d)...", cls._process.pid)
                cls._process.terminate()
            except Exception as exc:
                logger.warning("[Process Manager] Notice terminating Ollama process: %s", exc)
            finally:
                cls._process = None


ollama_process_manager = OllamaProcessManager()
