"""
Exercises ChatService end-to-end: real DB writes (in-memory SQLite),
real HTTP streaming (mock Ollama server) — everything except the
actual model is real.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import MessageRole
from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService
from app.services.llm import registry
from app.services.llm.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_stream_reply_persists_and_streams(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    # Point the registry's ollama provider at our mock server for this test.
    monkeypatch.setitem(
        registry._PROVIDERS, "ollama", lambda: OllamaProvider(base_url=mock_ollama_server)
    )

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="sub-1", email="chatter@example.com", full_name="Chatter", avatar_url=None
    )
    await db_session.commit()

    service = ChatService(db_session)
    conversation = await service.create_conversation(
        user_id=user.id, title=None, provider="ollama", model="qwen3:8b"
    )

    collected = ""
    async for chunk in service.stream_reply(conversation=conversation, user_content="hi there"):
        collected += chunk

    assert collected == "Hello there!"

    refreshed = await service.get_conversation(conversation_id=conversation.id, user_id=user.id)
    assert refreshed is not None
    assert len(refreshed.messages) == 2
    assert refreshed.messages[0].role == MessageRole.USER
    assert refreshed.messages[0].content == "hi there"
    assert refreshed.messages[1].role == MessageRole.ASSISTANT
    assert refreshed.messages[1].content == "Hello there!"
    assert refreshed.messages[1].error is None


@pytest.mark.asyncio
async def test_stream_reply_second_turn_has_correct_history_no_duplication(
    db_session: AsyncSession, mock_ollama_server: str, monkeypatch
) -> None:
    """Regression test: a prior bug queried prior history AFTER persisting
    the new user message, silently duplicating it in the prompt sent to
    the model. This proves message count and ordering stay correct across
    multiple turns."""
    monkeypatch.setitem(
        registry._PROVIDERS, "ollama", lambda: OllamaProvider(base_url=mock_ollama_server)
    )

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="sub-2", email="chatter2@example.com", full_name="Chatter2", avatar_url=None
    )
    await db_session.commit()

    service = ChatService(db_session)
    conversation = await service.create_conversation(
        user_id=user.id, title=None, provider="ollama", model="qwen3:8b"
    )

    async for _ in service.stream_reply(conversation=conversation, user_content="first message"):
        pass
    async for _ in service.stream_reply(conversation=conversation, user_content="second message"):
        pass

    refreshed = await service.get_conversation(conversation_id=conversation.id, user_id=user.id)
    assert refreshed is not None
    # 2 user turns + 2 assistant replies = 4 messages, never duplicated.
    assert len(refreshed.messages) == 4
    assert [m.content for m in refreshed.messages] == [
        "first message",
        "Hello there!",
        "second message",
        "Hello there!",
    ]
