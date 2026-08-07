"""
Memory service with update, type filter, pin, and archive support.
"""
import asyncio
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.vector_store import VectorStore
from app.models.memory import Memory, MemoryType
from app.repositories.memory_repository import MemoryRepository
from app.services.embeddings.registry import get_embedding_provider

COLLECTION_NAME = "memories"


class MemoryService:
    def __init__(self, session: AsyncSession, *, embedding_provider_name: str | None = None) -> None:
        self._session = session
        self._memories = MemoryRepository(session)
        self._vector_store = VectorStore(COLLECTION_NAME)
        self._embeddings = get_embedding_provider(embedding_provider_name)

    async def create_memory(
        self,
        *,
        user_id: int,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        agent_id: int | None = None,
        is_pinned: bool = False,
    ) -> Memory:
        memory = await self._memories.create(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            agent_id=agent_id,
            is_pinned=is_pinned,
        )

        vectors = await asyncio.to_thread(self._embeddings.embed, [content])
        vector = vectors[0]
        metadata: dict = {"user_id": user_id}
        if agent_id is not None:
            metadata["agent_id"] = agent_id

        self._vector_store.upsert(
            ids=[str(memory.id)],
            embeddings=[vector],
            documents=[content],
            metadatas=[metadata],
        )

        await self._session.commit()
        return memory

    async def update_memory(
        self,
        *,
        memory_id: int,
        user_id: int,
        content: str | None = None,
        memory_type: MemoryType | None = None,
        is_pinned: bool | None = None,
        is_archived: bool | None = None,
    ) -> Memory:
        memory = await self._memories.get_by_id(memory_id, user_id=user_id)
        if memory is None:
            raise ValueError("Memory entry not found")

        updated = await self._memories.update(
            memory,
            content=content,
            memory_type=memory_type,
            is_pinned=is_pinned,
            is_archived=is_archived,
        )

        if content is not None:
            vectors = await asyncio.to_thread(self._embeddings.embed, [content])
            vector = vectors[0]
            metadata: dict = {"user_id": user_id}
            if updated.agent_id is not None:
                metadata["agent_id"] = updated.agent_id
            self._vector_store.upsert(
                ids=[str(updated.id)],
                embeddings=[vector],
                documents=[content],
                metadatas=[metadata],
            )

        await self._session.commit()
        return updated

    async def search_memories(
        self, *, user_id: int, query: str, top_k: int = 3
    ) -> list[tuple[Memory, float]]:
        if not query.strip():
            return []

        query_vectors = await asyncio.to_thread(self._embeddings.embed, [query])
        query_vector = query_vectors[0]
        matches = self._vector_store.query(
            query_embedding=query_vector, top_k=top_k, where={"user_id": user_id}
        )
        if not matches:
            return []

        matched_ids = [int(m["id"]) for m in matches]
        memories = await self._memories.get_many_by_ids(matched_ids, user_id=user_id)
        memory_by_id = {m.id: m for m in memories}

        results = []
        for match in matches:
            memory = memory_by_id.get(int(match["id"]))
            if memory is not None:
                results.append((memory, match["distance"]))
        return results

    async def list_memories(
        self,
        *,
        user_id: int,
        memory_type: str | None = None,
        is_archived: bool | None = False,
        is_pinned: bool | None = None,
    ) -> Sequence[Memory]:
        return await self._memories.list_for_user(
            user_id, memory_type=memory_type, is_archived=is_archived, is_pinned=is_pinned
        )

    async def get_memory(self, *, memory_id: int, user_id: int) -> Memory | None:
        return await self._memories.get_by_id(memory_id, user_id=user_id)

    async def delete_memory(self, *, memory: Memory) -> None:
        self._vector_store.delete([str(memory.id)])
        await self._memories.delete(memory)
        await self._session.commit()
