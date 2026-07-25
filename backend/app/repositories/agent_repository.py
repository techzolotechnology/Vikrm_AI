from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: int, **fields) -> Agent:
        agent = Agent(user_id=user_id, **fields)
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def get_by_id(self, agent_id: int, *, user_id: int) -> Agent | None:
        result = await self._session.execute(
            select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int, *, include_archived: bool = False) -> list[Agent]:
        query = select(Agent).where(Agent.user_id == user_id)
        if not include_archived:
            query = query.where(Agent.status == AgentStatus.ACTIVE)
        query = query.order_by(Agent.updated_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, agent: Agent, **fields) -> Agent:
        for key, value in fields.items():
            if value is not None:
                setattr(agent, key, value)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def delete(self, agent: Agent) -> None:
        await self._session.delete(agent)
        await self._session.flush()
