"""
Proves agents aren't just stored config: creating a conversation from
an agent must inject its system prompt into the model's message
history and use its temperature — checked against what the mock
Ollama server actually received, not just what ChatService claims
to send.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.agent_repository import AgentRepository
from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService, ChatServiceError
from app.services.llm import registry
from app.services.llm.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_conversation_from_agent_injects_system_prompt_and_temperature(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    captured_requests: list[dict] = []

    # Wrap the provider to capture exactly what gets sent, proving the
    # system prompt and temperature really reach the model call.
    class CapturingProvider(OllamaProvider):
        async def stream_chat(self, *, messages, model, temperature=0.7):
            captured_requests.append(
                {
                    "messages": [(m.role, m.content) for m in messages],
                    "model": model,
                    "temperature": temperature,
                }
            )
            async for chunk in super().stream_chat(
                messages=messages, model=model, temperature=temperature
            ):
                yield chunk

    monkeypatch.setitem(
        registry._PROVIDERS,
        "ollama",
        lambda: CapturingProvider(base_url=mock_ollama_server),
    )

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="sub-agent", email="agentuser@example.com", full_name="Agent User", avatar_url=None
    )
    await db_session.commit()

    agents = AgentRepository(db_session)
    agent = await agents.create(
        user_id=user.id,
        name="Research Assistant",
        instructions="You are a meticulous research assistant.",
        goal="Always cite sources.",
        personality=None,
        provider="ollama",
        model="qwen3:8b",
        temperature=0.2,
        max_tokens=1024,
    )
    await db_session.commit()

    service = ChatService(db_session)
    conversation = await service.create_conversation(
        user_id=user.id, title=None, provider=None, model=None, agent_id=agent.id
    )

    # Agent settings should have seeded the conversation.
    assert conversation.title == "Research Assistant"
    assert conversation.provider == "ollama"
    assert conversation.model == "qwen3:8b"
    assert conversation.agent_id == agent.id

    async for _ in service.stream_reply(conversation=conversation, user_content="hi"):
        pass

    assert len(captured_requests) == 1
    request = captured_requests[0]
    assert request["temperature"] == 0.2
    assert request["messages"][0][0] == "system"
    assert "meticulous research assistant" in request["messages"][0][1]
    assert "cite sources" in request["messages"][0][1]
    assert request["messages"][-1] == ("user", "hi")


@pytest.mark.asyncio
async def test_creating_conversation_with_nonexistent_agent_raises(
    db_session: AsyncSession,
) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="sub-x", email="x@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = ChatService(db_session)
    with pytest.raises(ChatServiceError, match="Agent not found"):
        await service.create_conversation(
            user_id=user.id, title=None, provider=None, model=None, agent_id=9999
        )


@pytest.mark.asyncio
async def test_agent_belonging_to_another_user_cannot_be_used(
    db_session: AsyncSession,
) -> None:
    users = UserRepository(db_session)
    owner = await users.create(
        google_sub="owner", email="owner@example.com", full_name=None, avatar_url=None
    )
    intruder = await users.create(
        google_sub="intruder", email="intruder@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    agents = AgentRepository(db_session)
    agent = await agents.create(user_id=owner.id, name="Private Agent")
    await db_session.commit()

    service = ChatService(db_session)
    with pytest.raises(ChatServiceError, match="Agent not found"):
        await service.create_conversation(
            user_id=intruder.id, title=None, provider=None, model=None, agent_id=agent.id
        )
