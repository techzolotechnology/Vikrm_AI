from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, MemoryType


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        content: str,
        memory_type: MemoryType,
        agent_id: int | None = None,
        is_pinned: bool = False,
        is_archived: bool = False,
    ) -> Memory:
        memory = Memory(
            user_id=user_id,
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            is_pinned=is_pinned,
            is_archived=is_archived,
        )
        self._session.add(memory)
        await self._session.flush()
        await self._session.refresh(memory)
        return memory

    async def get_by_id(self, memory_id: int, *, user_id: int) -> Memory | None:
        result = await self._session.execute(
            select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_many_by_ids(self, memory_ids: list[int], *, user_id: int) -> list[Memory]:
        if not memory_ids:
            return []
        result = await self._session.execute(
            select(Memory).where(Memory.id.in_(memory_ids), Memory.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_for_user(
        self,
        user_id: int,
        *,
        memory_type: str | None = None,
        is_archived: bool | None = False,
        is_pinned: bool | None = None,
    ) -> Sequence[Memory]:
        stmt = select(Memory).where(Memory.user_id == user_id)

        if is_archived is not None:
            stmt = stmt.where(Memory.is_archived == is_archived)
        if is_pinned is not None:
            stmt = stmt.where(Memory.is_pinned == is_pinned)
        if memory_type is not None:
            stmt = stmt.where(Memory.memory_type == memory_type)

        stmt = stmt.order_by(Memory.is_pinned.desc(), Memory.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        memory: Memory,
        *,
        content: str | None = None,
        memory_type: MemoryType | None = None,
        is_pinned: bool | None = None,
        is_archived: bool | None = None,
    ) -> Memory:
        if content is not None:
            memory.content = content
        if memory_type is not None:
            memory.memory_type = memory_type
        if is_pinned is not None:
            memory.is_pinned = is_pinned
        if is_archived is not None:
            memory.is_archived = is_archived
        await self._session.flush()
        return memory

    async def delete(self, memory: Memory) -> None:
        await self._session.delete(memory)
        await self._session.flush()
