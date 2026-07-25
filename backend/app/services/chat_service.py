"""
Chat service.

`stream_reply` is the core of Milestone 3: it persists the user's
message immediately (so it survives even if streaming fails), creates
an empty assistant message row, then streams provider chunks — yielding
each chunk to the caller (the SSE endpoint) while incrementally
appending to the assistant message in the DB. If the provider errors
mid-stream, the partial content is kept and the error reason is
recorded on the message rather than silently discarding what was
already generated.
"""
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.agent_service import build_system_prompt
from app.services.llm.base import ChatMessage, ProviderError
from app.services.llm.registry import get_provider
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService


class ChatServiceError(Exception):
    pass


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)
        self._agents = AgentRepository(session)
        self._memories = MemoryService(session)
        self._rag = RagService(session)

    async def create_conversation(
        self,
        *,
        user_id: int,
        title: str | None,
        provider: str | None,
        model: str | None,
        agent_id: int | None = None,
    ) -> Conversation:
        resolved_provider = provider or settings.DEFAULT_LLM_PROVIDER
        resolved_model = model or settings.DEFAULT_LLM_MODEL
        resolved_title = title or "New Conversation"

        if agent_id is not None:
            agent = await self._agents.get_by_id(agent_id, user_id=user_id)
            if agent is None:
                raise ChatServiceError("Agent not found")
            # Agent settings are the default when a conversation is
            # explicitly started from one; an explicit provider/model
            # argument (if the caller passed one) still wins, so a user
            # can override an agent's model for one conversation.
            resolved_provider = provider or agent.provider
            resolved_model = model or agent.model
            resolved_title = title or agent.name

        conversation = await self._conversations.create(
            user_id=user_id,
            title=resolved_title,
            provider=resolved_provider,
            model=resolved_model,
            agent_id=agent_id,
        )
        await self._session.commit()
        return conversation

    async def list_conversations(self, *, user_id: int) -> list[Conversation]:
        return await self._conversations.list_for_user(user_id)

    async def get_conversation(self, *, conversation_id: int, user_id: int) -> Conversation | None:
        return await self._conversations.get_by_id(conversation_id, user_id=user_id)

    async def delete_conversation(self, conversation: Conversation) -> None:
        await self._conversations.delete(conversation)
        await self._session.commit()

    async def stream_reply(
        self, *, conversation: Conversation, user_content: str
    ) -> AsyncIterator[str]:
        # Fetch prior history BEFORE persisting the new user message —
        # otherwise the just-inserted message would be double-counted
        # (once from this query, once from the explicit append below).
        prior_messages = await self._messages.list_for_conversation(conversation.id)
        history = [ChatMessage(role=m.role.value, content=m.content) for m in prior_messages]

        temperature = 0.7
        if conversation.agent_id is not None:
            agent = await self._agents.get_by_id(conversation.agent_id, user_id=conversation.user_id)
            if agent is not None:
                system_prompt = build_system_prompt(agent)
                if system_prompt and not any(m.role == "system" for m in history):
                    history.insert(0, ChatMessage(role="system", content=system_prompt))
                temperature = agent.temperature

        # Surface relevant long-term memories as additional context —
        # a separate system message from the agent's own prompt, so a
        # memory-free agent still benefits from anything the user has
        # explicitly saved to memory across all their conversations.
        relevant_memories = await self._memories.search_memories(
            user_id=conversation.user_id, query=user_content, top_k=settings.MEMORY_SEARCH_TOP_K
        )
        if relevant_memories:
            memory_lines = "\n".join(f"- {memory.content}" for memory, _distance in relevant_memories)
            history.insert(
                0,
                ChatMessage(
                    role="system",
                    content=f"Relevant information you remember about this user:\n{memory_lines}",
                ),
            )

        # Surface relevant document excerpts with source citations —
        # a separate system message from memory, so the model (and a
        # UI inspecting message roles) can distinguish "what the user
        # told us" from "what's in their uploaded documents."
        relevant_chunks = await self._rag.search_chunks(
            user_id=conversation.user_id, query=user_content, top_k=settings.MEMORY_SEARCH_TOP_K
        )
        if relevant_chunks:
            citation_lines = "\n".join(
                f"[{chunk['metadata']['filename']}]: {chunk['document']}" for chunk in relevant_chunks
            )
            history.insert(
                0,
                ChatMessage(
                    role="system",
                    content=(
                        "Relevant excerpts from the user's uploaded documents "
                        f"(cite the filename when referencing these):\n{citation_lines}"
                    ),
                ),
            )

        history.append(ChatMessage(role="user", content=user_content))

        await self._messages.create(
            conversation_id=conversation.id, role=MessageRole.USER, content=user_content
        )
        await self._session.commit()

        assistant_message: Message = await self._messages.create(
            conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=""
        )
        await self._session.commit()

        provider = get_provider(conversation.provider)

        try:
            async for chunk in provider.stream_chat(
                messages=history, model=conversation.model, temperature=temperature
            ):
                await self._messages.append_content(assistant_message, chunk)
                await self._session.commit()
                yield chunk
        except ProviderError as exc:
            assistant_message.error = str(exc)
            await self._session.commit()
            yield f"\n\n[error: {exc}]"
            raise ChatServiceError(str(exc)) from exc
        finally:
            await self._conversations.touch(conversation)
            await self._session.commit()
