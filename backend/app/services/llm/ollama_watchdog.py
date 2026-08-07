"""
Ollama Proactive Background Watchdog.

Periodically monitors Ollama health every 30 seconds.
If Ollama process or connection drops, triggers automatic process recovery
and HTTP client pool recreation.
"""
import asyncio
from typing import Optional

from app.core.logging import get_logger
from app.services.llm.ollama_process_manager import OllamaProcessManager
from app.services.llm.ollama_client_manager import ollama_client_manager

logger = get_logger(__name__)


class OllamaWatchdog:
    """
    Background Watchdog monitoring task.
    """

    def __init__(self, interval_seconds: float = 30.0) -> None:
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def _watchdog_loop(self) -> None:
        logger.info("[Watchdog Started] Background Ollama health watchdog activated (interval=%.0fs)", self.interval_seconds)
        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                if not self._running:
                    break

                is_healthy = await OllamaProcessManager.is_ollama_responsive()
                if not is_healthy:
                    logger.warning("[Watchdog Alert] Ollama server unresponsive on routine check. Executing auto-recovery...")
                    recovered = await OllamaProcessManager.ensure_ollama_running()
                    if recovered:
                        logger.info("[Watchdog Recovery] Ollama auto-recovery successful. Recreating HTTP client pool...")
                        await ollama_client_manager.get_client(force_recreate=True)
                    else:
                        logger.error("[Watchdog Recovery Failure] Ollama auto-recovery attempt failed.")
                else:
                    logger.debug("[Watchdog Check] Ollama server healthy.")

            except asyncio.CancelledError:
                logger.info("[Watchdog Stopped] Watchdog loop task cancelled.")
                break
            except Exception as exc:
                logger.warning("[Watchdog Notice] Error in watchdog loop: %s", exc)

    def start(self) -> None:
        """Start background watchdog loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._watchdog_loop())

    async def stop(self) -> None:
        """Stop background watchdog loop cleanly."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("[Watchdog Stopped] Ollama background watchdog shutdown cleanly.")


ollama_watchdog = OllamaWatchdog()
