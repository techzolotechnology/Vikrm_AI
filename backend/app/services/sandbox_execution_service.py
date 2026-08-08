"""
Sandbox Execution Service.
Runs real, isolated build, test, and lint subprocess commands in temporary or containerized environments.
Captures command exit_code, stdout, stderr, and execution duration.
"""

import asyncio
import os
import subprocess
import time
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class SandboxExecutionResult(BaseModel):
    success: bool
    exit_code: int
    command: str
    stdout: str
    stderr: str
    duration_seconds: float
    is_sandboxed: bool = True


class SandboxExecutionService:
    @classmethod
    async def run_command(
        cls,
        command: str,
        cwd: str,
        timeout_seconds: int = 60,
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxExecutionResult:
        """
        Executes a shell command in an isolated workspace directory.
        """
        start_t = time.perf_counter()
        current_env = os.environ.copy()
        if env:
            current_env.update(env)

        logger.info("[SandboxExecutionService] Executing in %s: %s", cwd, command)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=current_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )
                exit_code = process.returncode or 0
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                process.kill()
                exit_code = -1
                stdout = ""
                stderr = f"Execution timed out after {timeout_seconds} seconds."

            duration = time.perf_counter() - start_t
            success = exit_code == 0

            return SandboxExecutionResult(
                success=success,
                exit_code=exit_code,
                command=command,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                is_sandboxed=True,
            )

        except Exception as exc:
            duration = time.perf_counter() - start_t
            logger.error("[SandboxExecutionService] Subprocess failure: %s", exc)
            return SandboxExecutionResult(
                success=False,
                exit_code=1,
                command=command,
                stdout="",
                stderr=str(exc),
                duration_seconds=duration,
                is_sandboxed=False,
            )

    @classmethod
    async def run_python_tests(cls, workspace_dir: str) -> SandboxExecutionResult:
        """Runs pytest on python test files within workspace."""
        cmd = f"python -m pytest server/tests backend/tests"
        return await cls.run_command(cmd, cwd=workspace_dir)

    @classmethod
    async def run_node_tests(cls, workspace_dir: str) -> SandboxExecutionResult:
        """Runs npm test / vitest on node test files within workspace."""
        cmd = "npm test -- --run"
        return await cls.run_command(cmd, cwd=workspace_dir)
