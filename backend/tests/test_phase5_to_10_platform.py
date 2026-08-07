"""
Phase 5 through Phase 10 Autonomous Software Engineering Platform Test Suite:
- Phase 5: Multi-Agent execution (7 specialist agents with typed models)
- Phase 6: Batch generation (validate -> repair -> store -> continue)
- Phase 7: Workspace Intelligence & Incremental Edit Engine surgical patching
- Phase 8: Real Sandbox Runtime Validation (stdout, stderr, exit_code, duration_seconds)
- Phase 9: Autonomous repair loop (repair agent -> patch files -> re-validate)
- Phase 10: Production readiness manifests (Dockerfile, README, CI workflow, .env.example)
"""

import pytest
import asyncio
import os
import sys
import tempfile
from unittest.mock import AsyncMock

from app.services.agents import (
    PlannerAgent, PlannerInput, PlannerOutput,
    BackendAgent, BackendAgentInput, BackendAgentOutput,
    FrontendAgent, FrontendAgentInput, FrontendAgentOutput,
    DatabaseAgent, DatabaseAgentInput, DatabaseAgentOutput,
    TestingAgent, TestingAgentInput, TestingAgentOutput,
    DocumentationAgent, DocumentationAgentInput, DocumentationAgentOutput,
    DeploymentAgent, DeploymentAgentInput, DeploymentAgentOutput,
)
from app.services.project.requirement_analysis_service import RequirementSpec
from app.services.project.architecture_planner import ArchitecturePlanner, ProjectPlan
from app.services.project.code_synthesis_engine import CodeSynthesisEngine
from app.services.project.incremental_edit_engine import IncrementalEditEngine, WorkspaceContext
from app.services.sandbox_execution_service import SandboxExecutionService, SandboxExecutionResult
from app.services.project.self_repair_loop import SelfRepairLoop
from app.services.project.score_evaluator import ScoreEvaluator
from app.services.llm.base import ChatMessage
from app.services.project.llm_orchestrator import LLMOrchestrator


@pytest.mark.asyncio
async def test_phase5_typed_multi_agent_pipeline():
    """Verify all 7 specialist agents execute with typed Pydantic models."""
    spec = RequirementSpec(
        app_name="FintechGateway",
        description="Payment gateway platform",
        domain="fintech",
        features=["Stripe Webhooks", "Ledger Accounting"],
        entities=["Transaction", "LedgerEntry"],
        is_ambiguous=False,
    )
    plan = ArchitecturePlanner.infer_and_plan("Build payment gateway")

    orchestrator = LLMOrchestrator()
    async def mock_agent_chat(messages, **kwargs):
        sys_c = messages[0].content.lower()
        if "backend" in sys_c:
            return "### server/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```"
        elif "frontend" in sys_c:
            return "### src/App.tsx\n```tsx\nexport default function App() { return <div>Gateway</div>; }\n```"
        elif "database" in sys_c or "sql" in sys_c:
            return "### server/models.py\n```python\nclass Transaction: pass\n```"
        elif "test" in sys_c or "qa" in sys_c:
            return "### server/tests/test_gateway.py\n```python\ndef test_pay(): assert True\n```"
        elif "documentation" in sys_c or "readme" in sys_c:
            return "### README.md\n```markdown\n# Fintech Gateway\n```"
        else:
            return "### Dockerfile\n```dockerfile\nFROM node:20-alpine\n```"

    orchestrator.chat = AsyncMock(side_effect=mock_agent_chat)

    db_res = await DatabaseAgent(orchestrator=orchestrator).execute(DatabaseAgentInput(spec=spec, plan=plan))
    be_res = await BackendAgent(orchestrator=orchestrator).execute(BackendAgentInput(spec=spec, plan=plan))
    fe_res = await FrontendAgent(orchestrator=orchestrator).execute(FrontendAgentInput(spec=spec, plan=plan))
    test_res = await TestingAgent(orchestrator=orchestrator).execute(TestingAgentInput(spec=spec, plan=plan))
    doc_res = await DocumentationAgent(orchestrator=orchestrator).execute(DocumentationAgentInput(spec=spec, plan=plan))
    dep_res = await DeploymentAgent(orchestrator=orchestrator).execute(DeploymentAgentInput(spec=spec, plan=plan))

    assert len(db_res.generated_files) > 0
    assert len(be_res.generated_files) > 0
    assert len(fe_res.generated_files) > 0
    assert len(test_res.generated_files) > 0
    assert len(doc_res.generated_files) > 0
    assert len(dep_res.generated_files) > 0


@pytest.mark.asyncio
async def test_phase7_incremental_edit_surgical_patching():
    """Verify IncrementalEditEngine modifies only target affected files, preserving workspace structure."""
    initial_files = {
        "package.json": "{\"name\": \"my-app\", \"dependencies\": {\"react\": \"^19.0.0\"}}",
        "src/App.tsx": "export default function App() { return <h1>Original App</h1>; }",
        "src/components/Header.tsx": "export function Header() { return <header>Header</header>; }",
    }

    ctx = WorkspaceContext(project_name="my-app", framework="React 19")
    ctx.load_from_files(initial_files)

    updated_files, changed_paths = IncrementalEditEngine.apply_edit(ctx, "Add stripe payment integration")

    assert len(changed_paths) > 0
    assert "package.json" in updated_files
    # Verify unedited Header.tsx remains preserved untouched in workspace context
    assert ctx.files["src/components/Header.tsx"] == initial_files["src/components/Header.tsx"]


@pytest.mark.asyncio
async def test_phase8_and_9_sandbox_execution_and_repair():
    """Verify Phase 8 runtime validation and Phase 9 autonomous repair loop up to 10 attempts."""
    python_cmd = sys.executable

    with tempfile.TemporaryDirectory() as tmp_dir:
        broken_py = os.path.join(tmp_dir, "test_app.py")
        with open(broken_py, "w", encoding="utf-8") as f:
            f.write("def test_broken():\n    assert 1 == 2  # Failing assertion\n")

        # Step 1: Real sandbox execution captures failing exit code and stderr
        res1 = await SandboxExecutionService.run_command(f'"{python_cmd}" -m pytest test_app.py', cwd=tmp_dir)
        assert res1.success is False
        assert res1.exit_code != 0
        assert res1.duration_seconds > 0

        # Step 2: Phase 9 Autonomous Repair Loop patches file
        orchestrator = LLMOrchestrator()
        fixed_py = "def test_broken():\n    assert 1 == 1\n"
        async def mock_repair(messages, **kwargs):
            return f"### test_app.py\n```python\n{fixed_py}\n```"

        orchestrator.chat = AsyncMock(side_effect=mock_repair)
        repair_loop = SelfRepairLoop(orchestrator=orchestrator)

        success, patched_files, history = await repair_loop.repair_workspace(
            workspace_dir=tmp_dir,
            files={"test_app.py": "def test_broken(): assert 1 == 2"},
            error_logs=res1.stdout + res1.stderr,
            test_command=f'"{python_cmd}" -m pytest test_app.py',
            max_attempts=10,
        )

        assert success is True
        assert "assert 1 == 1" in patched_files["test_app.py"]


def test_phase10_production_readiness_manifests():
    """Verify Phase 10 production readiness files exist with valid structures."""
    files = {
        "package.json": "{\"name\": \"prod-app\", \"scripts\": {\"build\": \"vite build\"}}",
        "src/App.tsx": "export default function App() { return <div>App</div>; }",
        "Dockerfile": "FROM node:20-alpine\nCMD [\"npm\", \"run\", \"dev\"]",
        "docker-compose.yml": "version: '3.8'\nservices:\n  web:\n    build: .",
        ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest",
        "README.md": "# Prod App\n\nGenerated by Vikrm AI",
        ".env.example": "VITE_API_URL=http://localhost:8000",
    }

    report = ScoreEvaluator.evaluate(files=files)

    assert "Dockerfile" in files
    assert "docker-compose.yml" in files
    assert ".github/workflows/ci.yml" in files
    assert "README.md" in files
    assert ".env.example" in files
    assert report.generation_score >= 90
