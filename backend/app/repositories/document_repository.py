from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: int, filename: str, content_type: str) -> Document:
        document = Document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            status=DocumentStatus.PROCESSING,
        )
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def get_by_id(self, document_id: int, *, user_id: int) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[Document]:
        result = await self._session.execute(
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_ready(self, document: Document, *, char_count: int, chunk_count: int) -> None:
        document.status = DocumentStatus.READY
        document.char_count = char_count
        document.chunk_count = chunk_count
        await self._session.flush()

    async def mark_failed(self, document: Document, *, error: str) -> None:
        document.status = DocumentStatus.FAILED
        document.error = error
        await self._session.flush()

    async def rename(self, document: Document, new_filename: str) -> Document:
        document.filename = new_filename
        await self._session.flush()
        return document

    async def delete(self, document: Document) -> None:
        await self._session.delete(document)
        await self._session.flush()
