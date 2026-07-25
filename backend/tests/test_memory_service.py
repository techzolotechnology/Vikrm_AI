"""
Exercises MemoryService end-to-end against real (isolated, temp-dir)
ChromaDB storage and the deterministic embedding provider — genuine
vector upsert/query, not mocks.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import MemoryType
from app.repositories.user_repository import UserRepository
from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_create_and_list_memory(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="mem-1", email="mem1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = MemoryService(db_session)
    memory = await service.create_memory(
        user_id=user.id, content="The user prefers concise answers.", memory_type=MemoryType.PREFERENCE
    )

    assert memory.id is not None
    listed = await service.list_memories(user_id=user.id)
    assert len(listed) == 1
    assert listed[0].content == "The user prefers concise answers."


@pytest.mark.asyncio
async def test_semantic_search_ranks_relevant_memory_first(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="mem-2", email="mem2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = MemoryService(db_session)
    await service.create_memory(user_id=user.id, content="The user's favorite programming language is Python.")
    await service.create_memory(user_id=user.id, content="The user's dog is named Max.")
    await service.create_memory(user_id=user.id, content="The user lives in Salem, Tamil Nadu.")

    results = await service.search_memories(user_id=user.id, query="What programming language do I like?", top_k=1)

    assert len(results) == 1
    top_memory, _distance = results[0]
    assert "Python" in top_memory.content


@pytest.mark.asyncio
async def test_search_is_scoped_to_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user_a = await users.create(google_sub="a", email="a@example.com", full_name=None, avatar_url=None)
    user_b = await users.create(google_sub="b", email="b@example.com", full_name=None, avatar_url=None)
    await db_session.commit()

    service = MemoryService(db_session)
    await service.create_memory(user_id=user_a.id, content="User A likes cats.")
    await service.create_memory(user_id=user_b.id, content="User B likes cats.")

    results_a = await service.search_memories(user_id=user_a.id, query="cats", top_k=5)
    assert len(results_a) == 1
    assert results_a[0][0].content == "User A likes cats."


@pytest.mark.asyncio
async def test_delete_memory_removes_from_both_stores(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="mem-3", email="mem3@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = MemoryService(db_session)
    memory = await service.create_memory(user_id=user.id, content="Temporary fact to delete.")

    await service.delete_memory(memory=memory)

    listed = await service.list_memories(user_id=user.id)
    assert listed == []

    results = await service.search_memories(user_id=user.id, query="Temporary fact", top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_empty_query_returns_no_results(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="mem-4", email="mem4@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = MemoryService(db_session)
    await service.create_memory(user_id=user.id, content="Some memory.")

    results = await service.search_memories(user_id=user.id, query="   ", top_k=5)
    assert results == []
