"""
Phase 5 Multi-Agent Execution Acceptance Test Suite:
- Verification of 7 typed specialist agents: PlannerAgent, BackendAgent, FrontendAgent, DatabaseAgent, TestingAgent, DocumentationAgent, DeploymentAgent
- Verification of typed Pydantic models for agent-to-agent communication
- Verification of isolated prompt execution and structured outputs
"""

import pytest
import asyncio
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
from app.services.project.architecture_planner import ArchitecturePlanner, ProjectPlan, TechStack
from app.services.project.llm_orchestrator import LLMOrchestrator


@pytest.mark.asyncio
async def test_planner_agent_execution():
    """Verify PlannerAgent generates typed PlannerOutput with ProjectPlan and TaskNodes."""
    orchestrator = LLMOrchestrator()
    async def mock_plan_structured(messages, schema_model):
        stack = TechStack(framework="React 19", database="PostgreSQL")
        return ProjectPlan(
            name="TestApp",
            description="Test SaaS",
            domain="saas",
            complexity="Medium",
            tech_stack=stack,
            planned_files=10,
            estimated_files=10,
            modules=["Auth", "Billing"],
            folder_hierarchy=["src", "server"],
        )

    orchestrator.chat_structured = AsyncMock(side_effect=mock_plan_structured)
    planner = PlannerAgent(orchestrator=orchestrator)
    spec = RequirementSpec(
        app_name="TestApp",
        description="Test SaaS",
        domain="saas",
        features=["Auth", "Billing"],
        entities=["User", "Subscription"],
        is_ambiguous=False,
    )

    out: PlannerOutput = await planner.execute(PlannerInput(spec=spec))
    assert isinstance(out, PlannerOutput)
    assert out.plan.name == "TestApp" or len(out.tasks) > 0


@pytest.mark.asyncio
async def test_specialist_agents_typed_models_and_execution():
    """Verify Backend, Frontend, Database, Testing, Documentation, and Deployment agents execute with typed models."""
    spec = RequirementSpec(
        app_name="FintechCore",
        description="Banking ledger app",
        domain="fintech",
        features=["Wallet", "Transfers"],
        entities=["Account", "Transaction"],
        is_ambiguous=False,
    )
    plan = ArchitecturePlanner.infer_and_plan("Build banking ledger app")

    orchestrator = LLMOrchestrator()
    async def mock_agent_chat(messages, **kwargs):
        sys_content = messages[0].content.lower()
        if "backend" in sys_content:
            return "### server/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {}\n```"
        elif "frontend" in sys_content:
            return "### src/App.tsx\n```tsx\nexport default function App() { return <div>App</div>; }\n```"
        elif "database" in sys_content or "sql" in sys_content:
            return "### server/schema.py\n```python\nclass User:\n    pass\n```"
        elif "test" in sys_content or "qa" in sys_content:
            return "### server/tests/test_api.py\n```python\ndef test_ok(): assert True\n```"
        elif "documentation" in sys_content or "readme" in sys_content:
            return "### README.md\n```markdown\n# Fintech Core\n```"
        else:
            return "### Dockerfile\n```dockerfile\nFROM node:20-alpine\n```"

    orchestrator.chat = AsyncMock(side_effect=mock_agent_chat)

    # 1. DatabaseAgent
    db_agent = DatabaseAgent(orchestrator=orchestrator)
    db_out: DatabaseAgentOutput = await db_agent.execute(DatabaseAgentInput(spec=spec, plan=plan))
    assert isinstance(db_out, DatabaseAgentOutput)
    assert len(db_out.generated_files) > 0

    # 2. BackendAgent
    backend_agent = BackendAgent(orchestrator=orchestrator)
    be_out: BackendAgentOutput = await backend_agent.execute(BackendAgentInput(spec=spec, plan=plan))
    assert isinstance(be_out, BackendAgentOutput)
    assert len(be_out.generated_files) > 0

    # 3. FrontendAgent
    fe_agent = FrontendAgent(orchestrator=orchestrator)
    fe_out: FrontendAgentOutput = await fe_agent.execute(FrontendAgentInput(spec=spec, plan=plan))
    assert isinstance(fe_out, FrontendAgentOutput)
    assert len(fe_out.generated_files) > 0

    # 4. TestingAgent
    test_agent = TestingAgent(orchestrator=orchestrator)
    test_out: TestingAgentOutput = await test_agent.execute(TestingAgentInput(spec=spec, plan=plan))
    assert isinstance(test_out, TestingAgentOutput)
    assert len(test_out.generated_files) > 0

    # 5. DocumentationAgent
    doc_agent = DocumentationAgent(orchestrator=orchestrator)
    doc_out: DocumentationAgentOutput = await doc_agent.execute(DocumentationAgentInput(spec=spec, plan=plan))
    assert isinstance(doc_out, DocumentationAgentOutput)
    assert len(doc_out.generated_files) > 0

    # 6. DeploymentAgent
    dep_agent = DeploymentAgent(orchestrator=orchestrator)
    dep_out: DeploymentAgentOutput = await dep_agent.execute(DeploymentAgentInput(spec=spec, plan=plan))
    assert isinstance(dep_out, DeploymentAgentOutput)
    assert len(dep_out.generated_files) > 0
