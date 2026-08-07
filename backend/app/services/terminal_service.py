"""
Terminal Execution Sandbox Service.

Executes CLI commands (npm, python, pip, docker, git, etc.) in a safe subprocess context.
"""
import asyncio
import os
import shlex
from typing import Dict, List


class TerminalService:
    ALLOWED_COMMANDS = {
        "npm", "pnpm", "bun", "yarn",
        "python", "python3", "pip", "uv",
        "docker", "git", "maven", "mvn", "gradle", "./gradlew"
    }

    @classmethod
    async def execute_command(cls, command_str: str, cwd: str = ".") -> Dict[str, str]:
        parts = shlex.split(command_str.strip())
        if not parts:
            return {"stdout": "", "stderr": "Empty command", "exit_code": 1}

        cmd = parts[0].lower()
        if cmd not in cls.ALLOWED_COMMANDS:
            return {
                "stdout": "",
                "stderr": f"Command '{cmd}' is restricted. Allowed commands: {', '.join(sorted(cls.ALLOWED_COMMANDS))}",
                "exit_code": 1,
            }

        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd if os.path.exists(cwd) else "."
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=30.0)

            return {
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode or 0,
            }
        except asyncio.TimeoutError:
            return {"stdout": "", "stderr": "Execution timed out (30 seconds limit)", "exit_code": 124}
        except Exception as e:
            return {"stdout": "", "stderr": f"Execution error: {str(e)}", "exit_code": 1}
