"""
Python code execution tool.

Runs user-supplied code in a genuinely separate OS process (not
in-process exec()), so it can't touch the backend's own memory, import
its modules, or access its DB session/credentials by construction —
that's the actual security boundary here, not an attempt to filter
"dangerous" syntax the way the calculator tool does. On top of process
isolation:
- Hard wall-clock timeout (default 5s), the process is killed on expiry.
- Output is captured and truncated, never streamed to a shell.
- Runs with `-I` (isolated mode: ignores PYTHONPATH/user site-packages
  and env-based config that could otherwise be used to inject behavior).
- No network access is granted by this tool itself, though on a shared
  host without additional container/network isolation, the subprocess
  still shares the machine's network namespace — see the module-level
  caveat below.

This is a reasonable, honest sandbox for a *self-hosted, single-tenant*
deployment where the person running Vikrm is also the person whose
code executes. It is explicitly NOT a security boundary suitable for
running untrusted code from strangers in a multi-tenant SaaS — that
needs real isolation (gVisor, Firecracker microVMs, or an ephemeral
per-execution container with no host network/filesystem access), which
is out of scope for this milestone and should be added before Vikrm is
ever exposed to untrusted multi-tenant workflows.
"""
import asyncio
import sys
import tempfile
from pathlib import Path

from app.services.tools.base import Tool, ToolContext, ToolError

EXECUTION_TIMEOUT_SECONDS = 5
MAX_OUTPUT_CHARS = 4000


class PythonExecutorTool(Tool):
    name = "python_executor"
    description = (
        "Executes a Python code snippet in an isolated subprocess and returns stdout/stderr. "
        f"Timeout: {EXECUTION_TIMEOUT_SECONDS}s. Not a hardened multi-tenant sandbox — see module docs."
    )

    async def run(self, input_text: str, *, context: ToolContext | None = None) -> str:
        code = input_text.strip()
        if not code:
            raise ToolError("No code provided")

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "snippet.py"
            script_path.write_text(code, encoding="utf-8")

            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-I",  # isolated mode: ignore PYTHONPATH, user site-packages, PYTHON* env vars
                    str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=EXECUTION_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError as exc:
                process.kill()
                await process.wait()
                raise ToolError(
                    f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s"
                ) from exc

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        if process.returncode != 0:
            error_output = (stderr_text or "Unknown error").strip()
            raise ToolError(f"Script exited with code {process.returncode}: {error_output[:1000]}")

        output = stdout_text.strip()
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "... [truncated]"
        return output or "(no output)"
