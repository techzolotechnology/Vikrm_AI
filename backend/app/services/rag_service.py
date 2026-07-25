"""
RAG service.

`process_upload` runs synchronously within the request (parse → chunk →
embed → store) rather than via a background job queue. For the file
sizes a chat platform's knowledge base realistically handles this is
fast enough to not need async job infrastructure yet; Milestone 7's
workflow engine is where genuine background/long-running execution
gets built, and large-document processing can move onto that queue
then without changing this service's public interface.
"""
from sqlalchemy.ext.asyncio import AsyncSession

import asyncio

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

    async def list_documents(self, *, user_id: int) -> list[Document]:
        return await self._documents.list_for_user(user_id)

    async def get_document(self, *, document_id: int, user_id: int) -> Document | None:
        return await self._documents.get_by_id(document_id, user_id=user_id)

    async def delete_document(self, *, document: Document) -> None:
        self._vector_store.delete_where({"document_id": document.id})
        await self._documents.delete(document)
        await self._session.commit()
