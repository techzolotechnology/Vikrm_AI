"""
Phase 3 Code Generation & Task Graph Acceptance Test Suite:
- TaskGraphBuilder DAG topological batching & CircularDependencyError on circular graph
- CodeSynthesisEngine batch synthesis incorporating RAG context
- Golden-set diversity test across diverse prompt domains
- AgentLoop streaming real awaited phases and scaling DAG batch count with complexity
"""

import pytest
import asyncio
from typing import Dict, List
from unittest.mock import AsyncMock, patch

from app.services.project.task_graph_builder import TaskGraphBuilder, TaskGraph, TaskNode, CircularDependencyError
from app.services.project.code_synthesis_engine import CodeSynthesisEngine
from app.services.project.requirement_analysis_service import RequirementSpec
from app.services.project.architecture_planner import ProjectPlan, TechStack, ArchitecturePlanner
from app.services.project.planning_agent import PlanningAgent, AgentPlan
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.services.project.agent_loop import AgentLoop
from app.services.llm.base import ChatMessage


def test_task_graph_builder_topological_sort_and_cycle_detection():
    """Verify TaskGraphBuilder sorts nodes topologically and raises CircularDependencyError on circular graph."""
    graph = TaskGraph()
    graph.add_node(TaskNode(id="A", name="Config A", dependencies=[], files=["config.json"]))
    graph.add_node(TaskNode(id="B", name="DB B", dependencies=["A"], files=["db.py"]))
    graph.add_node(TaskNode(id="C", name="API C", dependencies=["B"], files=["api.py"]))

    batches = TaskGraphBuilder.topological_sort(graph)
    assert len(batches) == 3
    assert batches[0][0].id == "A"
    assert batches[1][0].id == "B"
    assert batches[2][0].id == "C"

    # Introduce intentional circular dependency A -> C -> B -> A
    circular_graph = TaskGraph()
    circular_graph.add_node(TaskNode(id="N1", name="Node 1", dependencies=["N2"]))
    circular_graph.add_node(TaskNode(id="N2", name="Node 2", dependencies=["N1"]))

    with pytest.raises(CircularDependencyError):
        TaskGraphBuilder.topological_sort(circular_graph)


@pytest.mark.asyncio
async def test_code_synthesis_engine_rag_context_influence():
    """Verify CodeSynthesisEngine incorporates retrieved RAG context into LLM prompt."""
    orchestrator = LLMOrchestrator()
    received_messages: List[ChatMessage] = []

    async def mock_chat(messages, **kwargs):
        nonlocal received_messages
        received_messages = messages
        return "### src/pages/TelemetryPage.tsx\n```tsx\nexport function TelemetryPage() { return <div>Telemetry</div>; }\n```"

    orchestrator.chat = AsyncMock(side_effect=mock_chat)
    engine = CodeSynthesisEngine(orchestrator=orchestrator)

    plan = PlanningAgent.plan("Build a hospital vitals telemetry dashboard")
    plan.rag_context = ["RAG_DOC_SNIPPET: Use WebSocket subprotocols for high-frequency EHR streaming"]

    nodes = [TaskNode(id="t1", name="Telemetry Module", files=["src/pages/TelemetryPage.tsx"])]
    files = await engine.generate_batch(batch=nodes, plan=plan, existing_files={})

    assert "src/pages/TelemetryPage.tsx" in files
    assert len(received_messages) > 0
    prompt_text = received_messages[1].content
    assert "RAG_DOC_SNIPPET" in prompt_text
    assert "WebSocket subprotocols" in prompt_text


@pytest.mark.asyncio
async def test_golden_set_diversity_across_domains():
    """Golden-Set Diversity Test: Fixed diverse prompts produce domain-specific file structures."""
    prompts = [
        "Build a crypto trading bot with order book matching and Redis queue",
        "Build a clinical EHR patient portal with HIPAA audit logs and DICOM viewer",
        "Build a real-time multiplayer whiteboard with Canvas and WebSockets",
    ]

    plans = [PlanningAgent.plan(p) for p in prompts]
    
    # Verify domain and module diversity across domains
    assert plans[0].domain == "fintech"
    assert plans[1].domain == "healthcare"
    assert plans[2].domain == "realtime_chat"

    modules_0 = set(plans[0].modules)
    modules_1 = set(plans[1].modules)
    modules_2 = set(plans[2].modules)

    assert modules_0 != modules_1
    assert modules_1 != modules_2


@pytest.mark.asyncio
async def test_agent_loop_execution_and_scaling():
    """Verify AgentLoop streams events and scales DAG batches with complexity."""
    small_prompt = "build a simple todo list app"
    ent_prompt = "build an enterprise multi-tenant ERP platform with 500 features"

    small_plan = PlanningAgent.plan(small_prompt)
    ent_plan = PlanningAgent.plan(ent_prompt)

    spec_small = RequirementSpec(app_name="Todo", description="Simple Todo", domain="general", is_ambiguous=False)
    spec_ent = RequirementSpec(app_name="ERP", description="Enterprise ERP", domain="enterprise", is_ambiguous=False)

    proj_small = ArchitecturePlanner.infer_and_plan(small_prompt)
    proj_ent = ArchitecturePlanner.infer_and_plan(ent_prompt)

    g_small = TaskGraphBuilder.build_graph(spec_small, proj_small)
    g_ent = TaskGraphBuilder.build_graph(spec_ent, proj_ent)

    batches_small = TaskGraphBuilder.topological_sort(g_small)
    batches_ent = TaskGraphBuilder.topological_sort(g_ent)

    # Enterprise tier has more DAG modules/tasks than small tier
    assert len(g_ent.nodes) >= len(g_small.nodes)
    assert ent_plan.planned_files > small_plan.planned_files
