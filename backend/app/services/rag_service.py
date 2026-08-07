"""
RAG service with document rename and chunk preview support.
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.vector_store import VectorStore
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.embeddings.registry import get_embedding_provider
from app.services.rag.chunking import chunk_text
from app.services.rag.parsers import DocumentParseError, UnsupportedFileTypeError, parse_document

COLLECTION_NAME = "documents"


class RagServiceError(Exception):
    pass


class RagService:
    def __init__(self, session: AsyncSession, *, embedding_provider_name: str | None = None) -> None:
        self._session = session
        self._documents = DocumentRepository(session)
        self._vector_store = VectorStore(COLLECTION_NAME)
        self._embeddings = get_embedding_provider(embedding_provider_name)

    async def process_upload(
        self, *, user_id: int, filename: str, content_type: str, content: bytes
    ) -> Document:
        document = await self._documents.create(
            user_id=user_id, filename=filename, content_type=content_type
        )
        await self._session.commit()

        try:
            text = parse_document(filename=filename, content=content)
            chunks = chunk_text(text)

            if not chunks:
                await self._documents.mark_failed(document, error="Document contained no extractable text")
                await self._session.commit()
                return document

            vectors = await asyncio.to_thread(self._embeddings.embed, chunks)
            ids = [f"{document.id}-{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "document_id": document.id,
                    "user_id": user_id,
                    "filename": filename,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]

            self._vector_store.upsert(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)

            await self._documents.mark_ready(document, char_count=len(text), chunk_count=len(chunks))
            await self._session.commit()
            return document

        except (UnsupportedFileTypeError, DocumentParseError) as exc:
            await self._documents.mark_failed(document, error=str(exc))
            await self._session.commit()
            return document

    async def rename_document(self, *, document_id: int, user_id: int, new_filename: str) -> Document:
        doc = await self._documents.get_by_id(document_id, user_id=user_id)
        if doc is None:
            raise RagServiceError("Document not found")
        renamed = await self._documents.rename(doc, new_filename)
        await self._session.commit()
        return renamed

    async def search_chunks(
        self, *, user_id: int, query: str, top_k: int = 4
    ) -> list[dict]:
        if not query.strip():
            return []

        query_vectors = await asyncio.to_thread(self._embeddings.embed, [query])
        query_vector = query_vectors[0]
        matches = self._vector_store.query(
            query_embedding=query_vector, top_k=top_k, where={"user_id": user_id}
        )
        return matches

    async def get_document_chunks_preview(self, *, document_id: int, user_id: int) -> list[dict]:
        doc = await self._documents.get_by_id(document_id, user_id=user_id)
        if doc is None:
            return []
        matches = self._vector_store.query(
            query_embedding=[0.0] * 384, top_k=20, where={"document_id": document_id, "user_id": user_id}
        )
        return matches

    async def list_documents(self, *, user_id: int) -> list[Document]:
        return await self._documents.list_for_user(user_id)

    async def get_document(self, *, document_id: int, user_id: int) -> Document | None:
        return await self._documents.get_by_id(document_id, user_id=user_id)

    async def delete_document(self, *, document: Document) -> None:
        self._vector_store.delete_where({"document_id": document.id})
        await self._documents.delete(document)
        await self._session.commit()
