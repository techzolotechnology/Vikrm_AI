from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowRun


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: int, name: str, description: str | None, definition: dict) -> Workflow:
        workflow = Workflow(user_id=user_id, name=name, description=description, definition=definition)
        self._session.add(workflow)
        await self._session.flush()
        await self._session.refresh(workflow)
        return workflow

    async def get_by_id(self, workflow_id: int, *, user_id: int) -> Workflow | None:
        result = await self._session.execute(
            select(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[Workflow]:
        result = await self._session.execute(
            select(Workflow).where(Workflow.user_id == user_id).order_by(Workflow.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, workflow: Workflow, *, name: str | None, description: str | None, definition: dict | None
    ) -> Workflow:
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if definition is not None:
            workflow.definition = definition
        await self._session.flush()
        await self._session.refresh(workflow)
        return workflow

    async def delete(self, workflow: Workflow) -> None:
        await self._session.delete(workflow)
        await self._session.flush()


class WorkflowRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: WorkflowRun) -> WorkflowRun:
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get_by_id(self, run_id: int, *, user_id: int) -> WorkflowRun | None:
        result = await self._session.execute(
            select(WorkflowRun).where(WorkflowRun.id == run_id, WorkflowRun.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_workflow(self, workflow_id: int, *, user_id: int) -> list[WorkflowRun]:
        result = await self._session.execute(
            select(WorkflowRun)
            .where(WorkflowRun.workflow_id == workflow_id, WorkflowRun.user_id == user_id)
            .order_by(WorkflowRun.started_at.desc())
        )
        return list(result.scalars().all())
