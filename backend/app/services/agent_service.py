"""
Agent service.

`build_system_prompt` is the one piece of real "business logic" here:
it combines an agent's instructions/goal/personality into a single
system message. Kept as a pure function (not stored pre-concatenated
on the model) so editing any one field takes effect immediately on the
next message, without a migration or backfill.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus
from app.repositories.agent_repository import AgentRepository


class AgentServiceError(Exception):
    pass


def build_system_prompt(agent: Agent) -> str | None:
    parts: list[str] = []
    if agent.instructions:
        parts.append(agent.instructions.strip())
    if agent.goal:
        parts.append(f"Your goal: {agent.goal.strip()}")
    if agent.personality:
        parts.append(f"Personality and tone: {agent.personality.strip()}")

    if not parts:
        return None
    return "\n\n".join(parts)


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._agents = AgentRepository(session)

    async def create_agent(self, *, user_id: int, data: dict) -> Agent:
        agent = await self._agents.create(user_id=user_id, **data)
        await self._session.commit()
        return agent

    async def list_agents(self, *, user_id: int, include_archived: bool = False) -> list[Agent]:
        return await self._agents.list_for_user(user_id, include_archived=include_archived)

    async def get_agent(self, *, agent_id: int, user_id: int) -> Agent | None:
        return await self._agents.get_by_id(agent_id, user_id=user_id)

    async def update_agent(self, *, agent: Agent, data: dict) -> Agent:
        if "status" in data and data["status"] is not None:
            data["status"] = AgentStatus(data["status"])
        updated = await self._agents.update(agent, **data)
        await self._session.commit()
        return updated

    async def delete_agent(self, *, agent: Agent) -> None:
        await self._agents.delete(agent)
        await self._session.commit()

    async def duplicate_agent(self, *, agent: Agent, user_id: int) -> Agent:
        new_data = {
            "name": f"{agent.name} (Copy)",
            "description": agent.description,
            "system_prompt": agent.system_prompt,
            "instructions": agent.instructions,
            "goal": agent.goal,
            "personality": agent.personality,
            "provider": agent.provider,
            "model_name": agent.model_name,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "avatar_url": agent.avatar_url,
            "color": getattr(agent, "color", "#7C3AED"),
            "is_memory_enabled": getattr(agent, "is_memory_enabled", True),
            "status": AgentStatus.ACTIVE,
        }
        new_agent = await self._agents.create(user_id=user_id, **new_data)
        await self._session.commit()
        return new_agent

