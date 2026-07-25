"""
Proves AnalyticsService's numbers are actually correct — seeds known
quantities of real data across multiple services (chat, workflows,
teams, tools, documents) and asserts the aggregated counts match
exactly, not just that the endpoint responds.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentStatus
from app.repositories.agent_repository import AgentRepository
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService
from app.services.chat_service import ChatService
from app.services.rag_service import RagService
from app.services.tool_execution_service import ToolExecutionService


@pytest.mark.asyncio
async def test_dashboard_stats_reflect_real_seeded_data(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="stats-1", email="stats1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    # Seed two conversations via the real ChatService (not direct SQL inserts).
    chat_service = ChatService(db_session)
    await chat_service.create_conversation(user_id=user.id, title="Chat 1", provider="ollama", model="llama3.2")
    await chat_service.create_conversation(user_id=user.id, title="Chat 2", provider="ollama", model="llama3.2")

    # Seed agents.
    agents = AgentRepository(db_session)
    await agents.create(user_id=user.id, name="Agent A")
    await agents.create(user_id=user.id, name="Agent B")
    await db_session.commit()

    # Seed a document (one ready).
    rag_service = RagService(db_session)
    document = await rag_service.process_upload(
        user_id=user.id, filename="notes.txt", content_type="text/plain", content=b"Some real content here."
    )
    assert document.status == DocumentStatus.READY

    # Seed a tool execution (one success, one failure).
    tool_service = ToolExecutionService(db_session)
    await tool_service.execute(user_id=user.id, tool_name="calculator", input_text="2 + 2")
    await tool_service.execute(user_id=user.id, tool_name="calculator", input_text="not valid")

    analytics = AnalyticsService(db_session)
    stats = await analytics.get_dashboard_stats(user_id=user.id)

    assert stats.total_conversations == 2
    assert stats.total_agents == 2
    assert stats.total_documents == 1
    assert stats.documents_ready == 1
    assert stats.documents_failed == 0
    assert stats.total_tool_executions == 2
    assert stats.tool_executions_success == 1
    assert stats.tool_executions_failed == 1


@pytest.mark.asyncio
async def test_dashboard_stats_are_scoped_to_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user_a = await users.create(google_sub="a", email="a@example.com", full_name=None, avatar_url=None)
    user_b = await users.create(google_sub="b", email="b@example.com", full_name=None, avatar_url=None)
    await db_session.commit()

    agents = AgentRepository(db_session)
    await agents.create(user_id=user_a.id, name="A's Agent")
    await agents.create(user_id=user_b.id, name="B's Agent 1")
    await agents.create(user_id=user_b.id, name="B's Agent 2")
    await db_session.commit()

    analytics = AnalyticsService(db_session)
    stats_a = await analytics.get_dashboard_stats(user_id=user_a.id)
    stats_b = await analytics.get_dashboard_stats(user_id=user_b.id)

    assert stats_a.total_agents == 1
    assert stats_b.total_agents == 2


@pytest.mark.asyncio
async def test_recent_activity_includes_workflow_run_with_correct_status(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    from app.services.llm import registry
    from app.services.llm.ollama_provider import OllamaProvider
    from app.services.workflow_service import WorkflowService

    monkeypatch.setitem(registry._PROVIDERS, "ollama", lambda: OllamaProvider(base_url=mock_ollama_server))

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="activity-1", email="activity1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    workflow_service = WorkflowService(db_session)
    workflow = await workflow_service.create_workflow(
        user_id=user.id,
        name="Test Workflow",
        description=None,
        definition={
            "nodes": [
                {"id": "start", "type": "start", "data": {}},
                {"id": "out", "type": "output", "data": {"template": "{{input}}"}},
            ],
            "edges": [{"source": "start", "target": "out"}],
        },
    )
    await workflow_service.run_workflow(workflow=workflow, user_id=user.id, initial_input="test")

    analytics = AnalyticsService(db_session)
    activity = await analytics.get_recent_activity(user_id=user.id)

    workflow_activity = [a for a in activity if a.type == "workflow_run"]
    assert len(workflow_activity) == 1
    assert "Test Workflow" in workflow_activity[0].title
    assert workflow_activity[0].status == "completed"


@pytest.mark.asyncio
async def test_recent_activity_sorted_most_recent_first(db_session: AsyncSession) -> None:
    import asyncio

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="activity-2", email="activity2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    chat_service = ChatService(db_session)
    await chat_service.create_conversation(user_id=user.id, title="Older Chat", provider="ollama", model="llama3.2")
    await asyncio.sleep(0.01)
    await chat_service.create_conversation(user_id=user.id, title="Newer Chat", provider="ollama", model="llama3.2")

    analytics = AnalyticsService(db_session)
    activity = await analytics.get_recent_activity(user_id=user.id)

    titles = [a.title for a in activity]
    assert titles.index("Newer Chat") < titles.index("Older Chat")
