from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, MemoryType


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: int, content: str, memory_type: MemoryType, agent_id: int | None = None
    ) -> Memory:
        memory = Memory(user_id=user_id, agent_id=agent_id, content=content, memory_type=memory_type)
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

    async def list_for_user(self, user_id: int) -> list[Memory]:
        result = await self._session.execute(
            select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, memory: Memory) -> None:
        await self._session.delete(memory)
        await self._session.flush()
