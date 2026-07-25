from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_conversation(self, conversation_id: int) -> list[Message]:
        result = await self._session.execute(
            select(Message)
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
    ) -> Message:
        message = Message(
            conversation_id=conversation_id, role=role, content=content, error=error
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def append_content(self, message: Message, extra_content: str) -> None:
        message.content += extra_content
        await self._session.flush()
