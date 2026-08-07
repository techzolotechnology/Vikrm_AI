"""
Shell/Terminal executor tool implementation.
"""
import asyncio
import os

from app.services.tools.base import Tool, ToolContext, ToolError


class ShellExecutorTool(Tool):
    name = "shell_executor"
    description = "Executes safe shell/terminal commands within the local project workspace."

    async def run(self, input_text: str, context: ToolContext) -> str:
        command = input_text.strip()
        if not command:
            raise ToolError("Command string cannot be empty.")

        # Disallow dangerous commands
        forbidden = ["rm -rf /", "mkfs", "dd ", ":(){ :|:& };:"]
        if any(f in command for f in forbidden):
            raise ToolError("Command blocked for security safety constraints.")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)

            out_text = stdout.decode("utf-8", errors="replace").strip()
            err_text = stderr.decode("utf-8", errors="replace").strip()

            result_lines = []
            if out_text:
                result_lines.append(f"STDOUT:\n{out_text}")
            if err_text:
                result_lines.append(f"STDERR:\n{err_text}")
            if not result_lines:
                result_lines.append("Command executed with exit code 0 (no output).")

            return "\n\n".join(result_lines)
        except asyncio.TimeoutError:
            raise ToolError("Command execution timed out after 10 seconds.")
        except Exception as exc:
            raise ToolError(f"Shell execution failed: {exc}")
