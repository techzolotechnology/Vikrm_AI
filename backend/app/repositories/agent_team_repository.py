from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_team import AgentTeam, AgentTeamRun


class AgentTeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: int, name: str, description: str | None, manager_agent_id: int, member_agent_ids: list[int]
    ) -> AgentTeam:
        team = AgentTeam(
            user_id=user_id,
            name=name,
            description=description,
            manager_agent_id=manager_agent_id,
            member_agent_ids=member_agent_ids,
        )
        self._session.add(team)
        await self._session.flush()
        await self._session.refresh(team)
        return team

    async def get_by_id(self, team_id: int, *, user_id: int) -> AgentTeam | None:
        result = await self._session.execute(
            select(AgentTeam).where(AgentTeam.id == team_id, AgentTeam.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[AgentTeam]:
        result = await self._session.execute(
            select(AgentTeam).where(AgentTeam.user_id == user_id).order_by(AgentTeam.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, team: AgentTeam) -> None:
        await self._session.delete(team)
        await self._session.flush()


class AgentTeamRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: AgentTeamRun) -> AgentTeamRun:
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get_by_id(self, run_id: int, *, user_id: int) -> AgentTeamRun | None:
        result = await self._session.execute(
            select(AgentTeamRun).where(AgentTeamRun.id == run_id, AgentTeamRun.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_team(self, team_id: int, *, user_id: int) -> list[AgentTeamRun]:
        result = await self._session.execute(
            select(AgentTeamRun)
            .where(AgentTeamRun.team_id == team_id, AgentTeamRun.user_id == user_id)
            .order_by(AgentTeamRun.started_at.desc())
        )
        return list(result.scalars().all())
