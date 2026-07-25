from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_execution import ToolExecution


class ToolExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, execution: ToolExecution) -> ToolExecution:
        self._session.add(execution)
        await self._session.flush()
        await self._session.refresh(execution)
        return execution

    async def list_for_user(self, user_id: int, *, limit: int = 50) -> list[ToolExecution]:
        result = await self._session.execute(
            select(ToolExecution)
            .where(ToolExecution.user_id == user_id)
            .order_by(ToolExecution.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
