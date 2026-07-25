from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation


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
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id, title=title, provider=provider, model=model, agent_id=agent_id
        )
        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def get_by_id(self, conversation_id: int, *, user_id: int) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, conversation: Conversation) -> None:
        await self._session.delete(conversation)
        await self._session.flush()

    async def touch(self, conversation: Conversation) -> None:
        """Bump updated_at so recently-active conversations sort first."""
        from datetime import datetime, timezone

        conversation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
