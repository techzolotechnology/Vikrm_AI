import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_execution import ToolExecutionStatus
from app.repositories.user_repository import UserRepository
from app.services.tool_execution_service import ToolExecutionService
from app.services.workflow.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_execute_and_log_successful_tool_call(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="exec-1", email="exec1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = ToolExecutionService(db_session)
    execution = await service.execute(user_id=user.id, tool_name="calculator", input_text="5 * 5")

    assert execution.status == ToolExecutionStatus.SUCCESS
    assert execution.output_text == "25"
    assert execution.duration_ms >= 0

    history = await service.list_history(user_id=user.id)
    assert len(history) == 1
    assert history[0].id == execution.id


@pytest.mark.asyncio
async def test_execute_and_log_failed_tool_call(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="exec-2", email="exec2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = ToolExecutionService(db_session)
    execution = await service.execute(
        user_id=user.id, tool_name="calculator", input_text="not an expression"
    )

    assert execution.status == ToolExecutionStatus.FAILED
    assert execution.output_text is None
    assert execution.error is not None


@pytest.mark.asyncio
async def test_memory_search_tool_works_inside_a_real_workflow(db_session: AsyncSession) -> None:
    """The memory_search tool must work when invoked through the
    workflow engine's tool node, not just when called directly."""
    from app.services.memory_service import MemoryService

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="wf-mem", email="wfmem@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    memory_service = MemoryService(db_session)
    await memory_service.create_memory(
        user_id=user.id, content="The user's preferred programming language is Go."
    )

    definition = {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {
                "id": "search",
                "type": "tool",
                "data": {"tool_name": "memory_search", "input": "{{input}}"},
            },
            {"id": "out", "type": "output", "data": {"template": "{{search.output}}"}},
        ],
        "edges": [
            {"source": "start", "target": "search"},
            {"source": "search", "target": "out"},
        ],
    }

    engine = WorkflowEngine(db_session, user_id=user.id)
    result = await engine.execute(definition, initial_input="What language does the user prefer?")

    assert result.status == "completed"
    assert "Go" in result.final_output
