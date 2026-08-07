"""
Attachment repository for database queries.
"""
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_conversation(self, conversation_id: int) -> Sequence[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.conversation_id == conversation_id)
            .order_by(Attachment.created_at.asc())
        )
        res = await self._session.execute(stmt)
        return res.scalars().all()

    async def get_by_id(self, attachment_id: int, *, user_id: int) -> Attachment | None:
        stmt = select(Attachment).where(Attachment.id == attachment_id, Attachment.user_id == user_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(
        self,
        *,
        conversation_id: int,
        user_id: int,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        extracted_text: str | None = None,
        message_id: int | None = None,
    ) -> Attachment:
        attachment = Attachment(
            conversation_id=conversation_id,
            user_id=user_id,
            message_id=message_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            extracted_text=extracted_text,
        )
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def link_to_message(self, attachment: Attachment, message_id: int) -> None:
        attachment.message_id = message_id
        await self._session.flush()

    async def delete(self, attachment: Attachment) -> None:
        await self._session.delete(attachment)
        await self._session.flush()
