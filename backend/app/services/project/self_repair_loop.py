"""
Autonomous Self-Repair Loop Service.
Analyzes sandbox compilation/test errors via LLMOrchestrator and patches workspace files on disk until verification passes.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from app.services.sandbox_execution_service import SandboxExecutionService, SandboxExecutionResult
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.services.llm.base import ChatMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


class SelfRepairLoop:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def repair_workspace(
        self,
        workspace_dir: str,
        files: Dict[str, str],
        error_logs: str,
        test_command: str = "python -m pytest",
        max_attempts: int = 3,
    ) -> Tuple[bool, Dict[str, str], List[str]]:
        """
        Iteratively diagnoses and patches workspace files based on real execution errors.
        Returns (success: bool, patched_files: Dict[str, str], repair_history: List[str]).
        """
        patched_files = dict(files)
        history: List[str] = []

        for attempt in range(1, max_attempts + 1):
            history.append(f"Attempt {attempt}: Analyzing error logs...\n{error_logs[:300]}")

            prompt = (
                f"You are Vikrm AI Self-Repair Agent.\n"
                f"Execution Error Logs:\n{error_logs}\n\n"
                f"Current Workspace Files:\n" + "\n".join(f"- {p}" for p in list(patched_files.keys())[:20]) + "\n\n"
                f"Identify the root cause file and provide the fixed code. "
                f"Format response with markdown header ### path/to/file.ext followed by fixed code blocks."
            )

            messages = [
                ChatMessage(role="system", content="Fix the syntax or import errors described in the execution logs."),
                ChatMessage(role="user", content=prompt),
            ]

            try:
                response = await self.orchestrator.chat(messages=messages, temperature=0.1)
                file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
                matches = re.findall(file_regex, response)

                for m in matches:
                    p_clean = m[0].strip().replace("`", "").replace("./", "")
                    fixed_code = m[2].strip()
                    patched_files[p_clean] = fixed_code

                    # Write patch to disk if workspace_dir exists
                    full_path = os.path.join(workspace_dir, p_clean)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(fixed_code)

                # Re-verify via SandboxExecutionService
                res: SandboxExecutionResult = await SandboxExecutionService.run_command(test_command, cwd=workspace_dir)
                if res.success:
                    logger.info("[SelfRepairLoop] Repair succeeded on attempt %d", attempt)
                    return True, patched_files, history

                error_logs = res.stderr or res.stdout
            except Exception as exc:
                logger.warning("[SelfRepairLoop] Repair iteration warning: %s", exc)

        return False, patched_files, history
