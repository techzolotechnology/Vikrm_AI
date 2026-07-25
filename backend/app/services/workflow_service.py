"""
Workflow service.

`run_workflow` executes synchronously within the request — same
documented tradeoff as RagService's upload processing (Milestone 6):
Celery/background execution is a natural next evolution once workflows
commonly involve slow steps (multiple LLM calls, external APIs), but
isn't needed to prove the engine itself works correctly.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowRun, WorkflowRunStatus
from app.repositories.workflow_repository import WorkflowRepository, WorkflowRunRepository
from app.services.workflow.engine import WorkflowEngine


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._workflows = WorkflowRepository(session)
        self._runs = WorkflowRunRepository(session)

    async def create_workflow(
        self, *, user_id: int, name: str, description: str | None, definition: dict
    ) -> Workflow:
        workflow = await self._workflows.create(
            user_id=user_id, name=name, description=description, definition=definition
        )
        await self._session.commit()
        return workflow

    async def list_workflows(self, *, user_id: int) -> list[Workflow]:
        return await self._workflows.list_for_user(user_id)

    async def get_workflow(self, *, workflow_id: int, user_id: int) -> Workflow | None:
        return await self._workflows.get_by_id(workflow_id, user_id=user_id)

    async def update_workflow(
        self,
        *,
        workflow: Workflow,
        name: str | None,
        description: str | None,
        definition: dict | None,
    ) -> Workflow:
        updated = await self._workflows.update(
            workflow, name=name, description=description, definition=definition
        )
        await self._session.commit()
        return updated

    async def delete_workflow(self, *, workflow: Workflow) -> None:
        await self._workflows.delete(workflow)
        await self._session.commit()

    async def run_workflow(self, *, workflow: Workflow, user_id: int, initial_input: str) -> WorkflowRun:
        started_at = datetime.now(timezone.utc)
        engine = WorkflowEngine(self._session, user_id=user_id)

        try:
            result = await engine.execute(workflow.definition, initial_input=initial_input)
            status = (
                WorkflowRunStatus.COMPLETED
                if result.status == "completed"
                else WorkflowRunStatus.FAILED
            )
            steps_json = [
                {
                    "node_id": s.node_id,
                    "node_type": s.node_type,
                    "status": s.status,
                    "input_summary": s.input_summary,
                    "output": s.output,
                    "error": s.error,
                    "started_at": s.started_at.isoformat(),
                    "completed_at": s.completed_at.isoformat(),
                }
                for s in result.steps
            ]
            run = WorkflowRun(
                workflow_id=workflow.id,
                user_id=user_id,
                status=status,
                initial_input=initial_input,
                final_output=result.final_output,
                steps=steps_json,
                error=next((s["error"] for s in steps_json if s["error"]), None),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as exc:  # noqa: BLE001 — a validation/setup error before any node ran
            run = WorkflowRun(
                workflow_id=workflow.id,
                user_id=user_id,
                status=WorkflowRunStatus.FAILED,
                initial_input=initial_input,
                final_output=None,
                steps=[],
                error=str(exc),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        persisted_run = await self._runs.create(run)
        await self._session.commit()
        return persisted_run

    async def list_runs(self, *, workflow_id: int, user_id: int) -> list[WorkflowRun]:
        return await self._runs.list_for_workflow(workflow_id, user_id=user_id)

    async def get_run(self, *, run_id: int, user_id: int) -> WorkflowRun | None:
        return await self._runs.get_by_id(run_id, user_id=user_id)
