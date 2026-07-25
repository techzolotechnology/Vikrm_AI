"""
Exercises RagService end-to-end: real parsing, real chunking, real
ChromaDB storage (isolated temp dir, deterministic embedder) — the
entire pipeline except the production embedding model.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentStatus
from app.repositories.user_repository import UserRepository
from app.services.rag_service import RagService


@pytest.mark.asyncio
async def test_upload_txt_document_is_processed_and_searchable(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="rag-1", email="rag1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = RagService(db_session)
    document = await service.process_upload(
        user_id=user.id,
        filename="notes.txt",
        content_type="text/plain",
        content=b"Vikrm's default LLM provider is Ollama, running fully locally.",
    )

    assert document.status == DocumentStatus.READY
    assert document.chunk_count == 1
    assert document.char_count > 0

    results = await service.search_chunks(user_id=user.id, query="What is the default LLM provider?")
    assert len(results) == 1
    assert "Ollama" in results[0]["document"]
    assert results[0]["metadata"]["filename"] == "notes.txt"


@pytest.mark.asyncio
async def test_unsupported_file_type_marks_document_failed(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="rag-2", email="rag2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = RagService(db_session)
    document = await service.process_upload(
        user_id=user.id, filename="archive.zip", content_type="application/zip", content=b"PK\x03\x04"
    )

    assert document.status == DocumentStatus.FAILED
    assert document.error is not None
    assert "Unsupported" in document.error


@pytest.mark.asyncio
async def test_search_scoped_to_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user_a = await users.create(google_sub="a", email="a@example.com", full_name=None, avatar_url=None)
    user_b = await users.create(google_sub="b", email="b@example.com", full_name=None, avatar_url=None)
    await db_session.commit()

    service = RagService(db_session)
    await service.process_upload(
        user_id=user_a.id, filename="a.txt", content_type="text/plain", content=b"User A's secret document."
    )
    await service.process_upload(
        user_id=user_b.id, filename="b.txt", content_type="text/plain", content=b"User B's secret document."
    )

    results_a = await service.search_chunks(user_id=user_a.id, query="secret document")
    assert len(results_a) == 1
    assert results_a[0]["metadata"]["filename"] == "a.txt"


@pytest.mark.asyncio
async def test_delete_document_removes_chunks_from_search(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="rag-3", email="rag3@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = RagService(db_session)
    document = await service.process_upload(
        user_id=user.id,
        filename="temp.txt",
        content_type="text/plain",
        content=b"This document will be deleted shortly.",
    )

    await service.delete_document(document=document)

    listed = await service.list_documents(user_id=user.id)
    assert listed == []

    results = await service.search_chunks(user_id=user.id, query="deleted shortly")
    assert results == []


@pytest.mark.asyncio
async def test_multi_chunk_document_all_chunks_carry_correct_metadata(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="rag-4", email="rag4@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    long_text = " ".join(f"This is fact number {i} about the system." for i in range(150)).encode()

    service = RagService(db_session)
    document = await service.process_upload(
        user_id=user.id, filename="long.txt", content_type="text/plain", content=long_text
    )

    assert document.status == DocumentStatus.READY
    assert document.chunk_count > 1

    results = await service.search_chunks(user_id=user.id, query="fact number 100", top_k=10)
    assert len(results) > 0
    for r in results:
        assert r["metadata"]["document_id"] == document.id
        assert r["metadata"]["filename"] == "long.txt"
        assert isinstance(r["metadata"]["chunk_index"], int)
