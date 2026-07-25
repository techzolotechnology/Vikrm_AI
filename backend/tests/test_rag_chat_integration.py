"""
Proves RAG isn't just document storage: an uploaded document's content
must appear (with its filename as a citation) in the messages actually
sent to the model during a chat stream.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService
from app.services.llm import registry
from app.services.llm.ollama_provider import OllamaProvider
from app.services.rag_service import RagService


@pytest.mark.asyncio
async def test_relevant_document_chunk_is_injected_with_citation(
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
        google_sub="rag-chat", email="ragchat@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    rag_service = RagService(db_session)
    await rag_service.process_upload(
        user_id=user.id,
        filename="company_policy.txt",
        content_type="text/plain",
        content=b"Employees are entitled to 25 days of paid annual leave per year.",
    )

    chat_service = ChatService(db_session)
    conversation = await chat_service.create_conversation(
        user_id=user.id, title=None, provider="ollama", model="llama3.2"
    )

    async for _ in chat_service.stream_reply(
        conversation=conversation, user_content="How many days of paid leave do I get?"
    ):
        pass

    assert len(captured_requests) == 1
    system_messages = [m for role, m in captured_requests[0]["messages"] if role == "system"]
    assert any("25 days" in content for content in system_messages)
    assert any("company_policy.txt" in content for content in system_messages)


@pytest.mark.asyncio
async def test_no_documents_means_no_document_system_message(
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
        google_sub="no-docs", email="nodocs@example.com", full_name=None, avatar_url=None
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
