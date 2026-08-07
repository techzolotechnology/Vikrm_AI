from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message, MessageRole


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, message_id: int, conversation_id: int) -> Message | None:
        result = await self._session.execute(
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.id == message_id, Message.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def list_for_conversation(self, conversation_id: int) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        conversation_id: int,
        role: MessageRole,
        content: str,
        error: str | None = None,
        is_bookmarked: bool = False,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            error=error,
            is_bookmarked=is_bookmarked,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def update_content(self, message: Message, new_content: str) -> Message:
        message.content = new_content
        message.edited_at = datetime.now(timezone.utc)
        await self._session.flush()
        return message

    async def toggle_bookmark(self, message: Message) -> Message:
        message.is_bookmarked = not message.is_bookmarked
        await self._session.flush()
        return message

    async def append_content(self, message: Message, extra_content: str) -> None:
        message.content += extra_content
        await self._session.flush()

    async def delete(self, message: Message) -> None:
        await self._session.delete(message)
        await self._session.flush()
