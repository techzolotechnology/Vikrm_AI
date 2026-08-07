from typing import Sequence
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        title: str,
        provider: str,
        model: str,
        agent_id: int | None = None,
        is_pinned: bool = False,
        is_archived: bool = False,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title,
            provider=provider,
            model=model,
            agent_id=agent_id,
            is_pinned=is_pinned,
            is_archived=is_archived,
        )
        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def get_by_id(self, conversation_id: int, *, user_id: int) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.attachments),
                selectinload(Conversation.attachments),
            )
            .execution_options(populate_existing=True)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        *,
        is_archived: bool | None = False,
        is_pinned: bool | None = None,
        search_query: str | None = None,
    ) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.attachments),
            )
            .where(Conversation.user_id == user_id)
        )

        if is_archived is not None:
            stmt = stmt.where(Conversation.is_archived == is_archived)
        if is_pinned is not None:
            stmt = stmt.where(Conversation.is_pinned == is_pinned)

        if search_query:
            pattern = f"%{search_query}%"
            stmt = stmt.outerjoin(Conversation.messages).where(
                or_(
                    Conversation.title.ilike(pattern),
                    Message.content.ilike(pattern),
                )
            ).distinct()

        stmt = stmt.order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        conversation: Conversation,
        *,
        title: str | None = None,
        is_pinned: bool | None = None,
        is_archived: bool | None = None,
        summary: str | None = None,
    ) -> Conversation:
        if title is not None:
            conversation.title = title
        if is_pinned is not None:
            conversation.is_pinned = is_pinned
        if is_archived is not None:
            conversation.is_archived = is_archived
        if summary is not None:
            conversation.summary = summary

        await self._session.flush()
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        await self._session.delete(conversation)
        await self._session.flush()

    async def touch(self, conversation: Conversation) -> None:
        from datetime import datetime, timezone

        conversation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
