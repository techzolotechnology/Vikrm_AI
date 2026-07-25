"""
Admin service.

Every method here requires the caller to already have passed
`require_admin` (enforced at the API layer, not here) — this service
has no additional authorization checks of its own, since "is this
caller an admin" is a single, already-solved concern from Milestone 2
and shouldn't be re-implemented per-service.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.agent_team import AgentTeam
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.memory import Memory
from app.models.tool_execution import ToolExecution
from app.models.user import User, UserRole
from app.models.workflow import Workflow


class AdminServiceError(Exception):
    pass


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_users(self) -> list[User]:
        result = await self._session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def get_user(self, user_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(
        self,
        *,
        target_user_id: int,
        acting_user_id: int,
        role: str | None,
        is_active: bool | None,
    ) -> User:
        if target_user_id == acting_user_id:
            if role is not None and role != UserRole.ADMIN.value:
                raise AdminServiceError("You cannot remove your own admin role")
            if is_active is False:
                raise AdminServiceError("You cannot deactivate your own account")

        user = await self.get_user(target_user_id)
        if user is None:
            raise AdminServiceError("User not found")

        if role is not None:
            user.role = UserRole(role)
        if is_active is not None:
            user.is_active = is_active

        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_system_stats(self) -> dict:
        """System-wide counts across ALL users — distinct from
        AnalyticsService (Milestone 11), which is always scoped to a
        single user's own data."""

        async def count(model) -> int:
            result = await self._session.execute(select(func.count()).select_from(model))
            return result.scalar_one()

        total_users = await count(User)
        active_users_result = await self._session.execute(
            select(func.count()).select_from(User).where(User.is_active.is_(True))
        )
        admin_count_result = await self._session.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
        )

        return {
            "total_users": total_users,
            "active_users": active_users_result.scalar_one(),
            "admin_users": admin_count_result.scalar_one(),
            "total_conversations": await count(Conversation),
            "total_agents": await count(Agent),
            "total_teams": await count(AgentTeam),
            "total_memories": await count(Memory),
            "total_documents": await count(Document),
            "total_workflows": await count(Workflow),
            "total_tool_executions": await count(ToolExecution),
        }
