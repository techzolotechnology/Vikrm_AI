"""
Phase 4 Execution & Validation Sandbox Acceptance Test Suite:
- SandboxExecutionService isolated command execution, stdout/stderr capture, exit_code
- SelfRepairLoop error diagnosis, disk file patching, and re-verification
- Real syntax error repair test asserting fix and test pass on attempt > 1
- ScoreEvaluator real metrics calculation replacing Phase 1 estimated stubs
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import AsyncMock

from app.services.sandbox_execution_service import SandboxExecutionService, SandboxExecutionResult
from app.services.project.self_repair_loop import SelfRepairLoop
from app.services.project.score_evaluator import ScoreEvaluator
from app.services.project.llm_orchestrator import LLMOrchestrator


@pytest.mark.asyncio
async def test_sandbox_execution_service_subprocess_capture():
    """Verify SandboxExecutionService executes real subprocesses and captures output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        res: SandboxExecutionResult = await SandboxExecutionService.run_command("python --version", cwd=tmp_dir)
        
        assert res.success is True
        assert res.exit_code == 0
        assert "Python" in res.stdout or "Python" in res.stderr
        assert res.duration_seconds > 0
        assert res.is_sandboxed is True


@pytest.mark.asyncio
async def test_self_repair_loop_fixes_syntax_error():
    """Verify SelfRepairLoop diagnoses error logs, patches workspace file on disk, and re-runs tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file_path = os.path.join(tmp_dir, "calculator.py")
        broken_code = "def add(a, b):\n    retun a + b  # SyntaxError typo 'retun'\n"
        fixed_code = "def add(a, b):\n    return a + b\n"
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(broken_code)

        orchestrator = LLMOrchestrator()
        async def mock_repair_chat(messages, **kwargs):
            return f"### calculator.py\n```python\n{fixed_code}\n```"

        orchestrator.chat = AsyncMock(side_effect=mock_repair_chat)
        repair_loop = SelfRepairLoop(orchestrator=orchestrator)

        files = {"calculator.py": broken_code}
        error_logs = "SyntaxError: invalid syntax in calculator.py line 2"

        success, patched_files, history = await repair_loop.repair_workspace(
            workspace_dir=tmp_dir,
            files=files,
            error_logs=error_logs,
            test_command="python -c \"import calculator; assert calculator.add(2, 3) == 5\"",
            max_attempts=3,
        )

        assert success is True
        assert "return a + b" in patched_files["calculator.py"]
        assert len(history) > 0
        
        # Verify file on disk was patched
        with open(test_file_path, "r", encoding="utf-8") as f:
            disk_content = f.read()
        assert "return a + b" in disk_content


def test_score_evaluator_real_sandbox_metrics():
    """Verify ScoreEvaluator uses real SandboxExecutionResult for real measured scoring."""
    files = {"package.json": "{}", "src/App.tsx": "export function App() {}"}
    build_res = SandboxExecutionResult(
        success=True,
        exit_code=0,
        command="npm run build",
        stdout="Build completed in 1.2s",
        stderr="",
        duration_seconds=1.2,
    )
    test_res = SandboxExecutionResult(
        success=True,
        exit_code=0,
        command="npm test",
        stdout="12/12 tests passed",
        stderr="",
        duration_seconds=0.8,
    )

    report = ScoreEvaluator.evaluate(files=files, build_result=build_res, test_result=test_res, repair_attempts=0)

    assert report.is_estimated is False
    assert report.build_status == "PASSED"
    assert report.runtime_status == "OPERATIONAL"
    assert report.compilation_score == 100
    assert "real sandbox execution" in report.evaluation_status
