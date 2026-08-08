"""
Exercises WorkflowEngine end-to-end: real node execution (LLM calls
against a mock Ollama server, real tool calls, real condition
branching) — not a simulation of what the engine would do.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm import registry
from app.services.llm.ollama_provider import OllamaProvider
from app.services.workflow.engine import WorkflowEngine, WorkflowValidationError


@pytest.mark.asyncio
async def test_linear_workflow_start_llm_output(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    monkeypatch.setitem(registry._PROVIDERS, "ollama", lambda: OllamaProvider(base_url=mock_ollama_server))

    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {
                "id": "llm1",
                "type": "llm",
                "data": {"provider": "ollama", "model": "qwen3:8b", "prompt": "Echo: {{input}}"},
            },
            {"id": "out", "type": "output", "data": {"template": "{{llm1.output}}"}},
        ],
        "edges": [
            {"source": "start", "target": "llm1"},
            {"source": "llm1", "target": "out"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="hello")

    assert result.status == "completed"
    assert result.final_output == "Hello there!"  # the mock Ollama server's fixed response
    assert [s.node_id for s in result.steps] == ["start", "llm1", "out"]
    assert all(s.status == "success" for s in result.steps)


@pytest.mark.asyncio
async def test_workflow_with_tool_node(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {"id": "calc", "type": "tool", "data": {"tool_name": "calculator", "input": "{{input}}"}},
            {"id": "out", "type": "output", "data": {"template": "Result: {{calc.output}}"}},
        ],
        "edges": [
            {"source": "start", "target": "calc"},
            {"source": "calc", "target": "out"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="6 * 7")

    assert result.status == "completed"
    assert result.final_output == "Result: 42"


@pytest.mark.asyncio
async def test_condition_branching_takes_true_path(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {
                "id": "check",
                "type": "condition",
                "data": {"left": "{{input}}", "operator": "contains", "right": "urgent"},
            },
            {"id": "true_out", "type": "output", "data": {"template": "HIGH PRIORITY: {{input}}"}},
            {"id": "false_out", "type": "output", "data": {"template": "normal: {{input}}"}},
        ],
        "edges": [
            {"source": "start", "target": "check"},
            {"source": "check", "target": "true_out", "branch": "true"},
            {"source": "check", "target": "false_out", "branch": "false"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="this is urgent")

    assert result.status == "completed"
    executed_ids = {s.node_id for s in result.steps}
    assert "true_out" in executed_ids
    assert "false_out" not in executed_ids  # the untaken branch must never execute
    assert result.final_output == "HIGH PRIORITY: this is urgent"


@pytest.mark.asyncio
async def test_condition_branching_takes_false_path(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {
                "id": "check",
                "type": "condition",
                "data": {"left": "{{input}}", "operator": "contains", "right": "urgent"},
            },
            {"id": "true_out", "type": "output", "data": {"template": "HIGH PRIORITY"}},
            {"id": "false_out", "type": "output", "data": {"template": "normal"}},
        ],
        "edges": [
            {"source": "start", "target": "check"},
            {"source": "check", "target": "true_out", "branch": "true"},
            {"source": "check", "target": "false_out", "branch": "false"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="just a regular message")

    executed_ids = {s.node_id for s in result.steps}
    assert "false_out" in executed_ids
    assert "true_out" not in executed_ids
    assert result.final_output == "normal"


@pytest.mark.asyncio
async def test_failed_node_stops_only_its_own_branch(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {"id": "bad_calc", "type": "tool", "data": {"tool_name": "calculator", "input": "not math"}},
            {"id": "unreachable", "type": "output", "data": {"template": "should never run"}},
        ],
        "edges": [
            {"source": "start", "target": "bad_calc"},
            {"source": "bad_calc", "target": "unreachable"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="")

    assert result.status == "failed"
    executed_ids = {s.node_id for s in result.steps}
    assert "bad_calc" in executed_ids
    assert "unreachable" not in executed_ids

    bad_step = next(s for s in result.steps if s.node_id == "bad_calc")
    assert bad_step.status == "failed"
    assert bad_step.error is not None


@pytest.mark.asyncio
async def test_missing_start_node_raises_validation_error(db_session: AsyncSession) -> None:
    definition = {"nodes": [{"id": "out", "type": "output", "data": {}}], "edges": []}

    engine = WorkflowEngine(db_session, user_id=1)
    with pytest.raises(WorkflowValidationError):
        await engine.execute(definition, initial_input="x")


@pytest.mark.asyncio
async def test_unknown_tool_name_fails_gracefully(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {"id": "bad_tool", "type": "tool", "data": {"tool_name": "nonexistent_tool", "input": "x"}},
        ],
        "edges": [{"source": "start", "target": "bad_tool"}],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="x")

    assert result.status == "failed"
    bad_step = next(s for s in result.steps if s.node_id == "bad_tool")
    assert "Unknown tool" in bad_step.error


@pytest.mark.asyncio
async def test_multi_node_pipeline_execution(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {"id": "calc", "type": "tool", "data": {"tool_name": "calculator", "input": "50 + 50"}},
            {
                "id": "check",
                "type": "condition",
                "data": {"left": "{{calc.output}}", "operator": "equals", "right": "100"},
            },
            {"id": "out", "type": "output", "data": {"template": "SUCCESS: {{calc.output}}"}},
        ],
        "edges": [
            {"source": "start", "target": "calc"},
            {"source": "calc", "target": "check"},
            {"source": "check", "target": "out", "branch": "true"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    result = await engine.execute(definition, initial_input="start test")

    assert result.status == "completed"
    assert [s.node_id for s in result.steps] == ["start", "calc", "check", "out"]
    assert result.final_output == "SUCCESS: 100"


@pytest.mark.asyncio
async def test_cycle_detection_raises_validation_error(db_session: AsyncSession) -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {"id": "node_a", "type": "tool", "data": {"tool_name": "calculator", "input": "1+1"}},
            {"id": "node_b", "type": "tool", "data": {"tool_name": "calculator", "input": "2+2"}},
        ],
        "edges": [
            {"source": "start", "target": "node_a"},
            {"source": "node_a", "target": "node_b"},
            {"source": "node_b", "target": "node_a"},  # Cycle!
        ],
    }

    engine = WorkflowEngine(db_session, user_id=1)
    with pytest.raises(WorkflowValidationError, match="Cycle detected"):
        await engine.execute(definition, initial_input="loop")

