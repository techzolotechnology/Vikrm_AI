"""
Proves memory isn't just stored config: a relevant memory must appear
in the messages actually sent to the model during a chat stream —
checked against what the mock Ollama server received.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService
from app.services.llm import registry
from app.services.llm.ollama_provider import OllamaProvider
from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_relevant_memory_is_injected_into_chat_stream(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    captured_requests: list[dict] = []

    class CapturingProvider(OllamaProvider):
        async def stream_chat(self, *, messages, model, temperature=0.7):
            captured_requests.append({"messages": [(m.role, m.content) for m in messages]})
            async for chunk in super().stream_chat(
                messages=messages, model=model, temperature=temperature
            ):
                yield chunk

    monkeypatch.setitem(
        registry._PROVIDERS, "ollama", lambda: CapturingProvider(base_url=mock_ollama_server)
    )

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="mem-chat", email="memchat@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    memory_service = MemoryService(db_session)
    await memory_service.create_memory(
        user_id=user.id, content="The user's favorite programming language is Rust."
    )
    await memory_service.create_memory(user_id=user.id, content="The user's dog is named Max.")

    chat_service = ChatService(db_session)
    conversation = await chat_service.create_conversation(
        user_id=user.id, title=None, provider="ollama", model="llama3.2"
    )

    async for _ in chat_service.stream_reply(
        conversation=conversation, user_content="What programming language do I prefer?"
    ):
        pass

    assert len(captured_requests) == 1
    system_messages = [m for role, m in captured_requests[0]["messages"] if role == "system"]
    assert any("Rust" in content for content in system_messages)


@pytest.mark.asyncio
async def test_no_memories_means_no_extra_system_message(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    captured_requests: list[dict] = []

    class CapturingProvider(OllamaProvider):
        async def stream_chat(self, *, messages, model, temperature=0.7):
            captured_requests.append({"messages": [(m.role, m.content) for m in messages]})
            async for chunk in super().stream_chat(
                messages=messages, model=model, temperature=temperature
            ):
                yield chunk

    monkeypatch.setitem(
        registry._PROVIDERS, "ollama", lambda: CapturingProvider(base_url=mock_ollama_server)
    )

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="no-mem", email="nomem@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    chat_service = ChatService(db_session)
    conversation = await chat_service.create_conversation(
        user_id=user.id, title=None, provider="ollama", model="llama3.2"
    )

    async for _ in chat_service.stream_reply(conversation=conversation, user_content="hello"):
        pass

    system_messages = [m for role, m in captured_requests[0]["messages"] if role == "system"]
    assert system_messages == []
