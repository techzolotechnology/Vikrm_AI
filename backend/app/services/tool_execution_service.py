"""
Tool execution service.

Wraps a direct (non-workflow) tool invocation with timing and a
persisted log row — used by `POST /tools/{name}/execute`, which exists
so a user can test a tool standalone (e.g. from a future "AI
Playground" UI) without building a whole workflow around it.

Workflow-triggered tool calls are *not* additionally logged here —
they're already fully recorded in `WorkflowRun.steps` (Milestone 7),
and duplicating that into this table would mean two sources of truth
for the same event. This table is specifically the log of standalone
tool executions.
"""
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_execution import ToolExecution, ToolExecutionStatus
from app.repositories.tool_execution_repository import ToolExecutionRepository
from app.services.tools.base import ToolContext, ToolError
from app.services.tools.registry import get_tool


class ToolExecutionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._executions = ToolExecutionRepository(session)

    async def execute(self, *, user_id: int, tool_name: str, input_text: str) -> ToolExecution:
        started = time.monotonic()
        context = ToolContext(user_id=user_id, session=self._session)

        try:
            tool = get_tool(tool_name)
            output = await tool.run(input_text, context=context)
            status = ToolExecutionStatus.SUCCESS
            error = None
        except ToolError as exc:
            output = None
            status = ToolExecutionStatus.FAILED
            error = str(exc)

        duration_ms = int((time.monotonic() - started) * 1000)

        execution = ToolExecution(
            user_id=user_id,
            tool_name=tool_name,
            input_text=input_text,
            output_text=output,
            status=status,
            error=error,
            duration_ms=duration_ms,
        )
        persisted = await self._executions.create(execution)
        await self._session.commit()
        return persisted

    async def list_history(self, *, user_id: int, limit: int = 50) -> list[ToolExecution]:
        return await self._executions.list_for_user(user_id, limit=limit)
