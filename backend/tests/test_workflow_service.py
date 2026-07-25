"""
Proves WorkflowService actually persists workflows and runs to the
database correctly — the engine tests cover execution logic in
isolation; these cover the CRUD + run-recording layer on top of it.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowRunStatus
from app.repositories.user_repository import UserRepository
from app.services.workflow_service import WorkflowService

SIMPLE_DEFINITION = {
    "nodes": [
        {"id": "start", "type": "start", "data": {}},
        {"id": "calc", "type": "tool", "data": {"tool_name": "calculator", "input": "{{input}}"}},
        {"id": "out", "type": "output", "data": {"template": "{{calc.output}}"}},
    ],
    "edges": [
        {"source": "start", "target": "calc"},
        {"source": "calc", "target": "out"},
    ],
}


@pytest.mark.asyncio
async def test_create_and_run_workflow_persists_correctly(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="wf-1", email="wf1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = WorkflowService(db_session)
    workflow = await service.create_workflow(
        user_id=user.id, name="Calc Workflow", description="Doubles numbers", definition=SIMPLE_DEFINITION
    )

    assert workflow.id is not None
    assert workflow.definition == SIMPLE_DEFINITION

    run = await service.run_workflow(workflow=workflow, user_id=user.id, initial_input="21 * 2")

    assert run.id is not None
    assert run.status == WorkflowRunStatus.COMPLETED
    assert run.final_output == "42"
    assert len(run.steps) == 3

    runs = await service.list_runs(workflow_id=workflow.id, user_id=user.id)
    assert len(runs) == 1
    assert runs[0].id == run.id

    fetched_run = await service.get_run(run_id=run.id, user_id=user.id)
    assert fetched_run is not None
    assert fetched_run.final_output == "42"


@pytest.mark.asyncio
async def test_run_from_another_user_is_not_visible(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    owner = await users.create(google_sub="owner", email="owner@example.com", full_name=None, avatar_url=None)
    intruder = await users.create(
        google_sub="intruder", email="intruder@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = WorkflowService(db_session)
    workflow = await service.create_workflow(
        user_id=owner.id, name="Private", description=None, definition=SIMPLE_DEFINITION
    )
    run = await service.run_workflow(workflow=workflow, user_id=owner.id, initial_input="1 + 1")

    fetched_by_intruder = await service.get_run(run_id=run.id, user_id=intruder.id)
    assert fetched_by_intruder is None

    fetched_workflow_by_intruder = await service.get_workflow(workflow_id=workflow.id, user_id=intruder.id)
    assert fetched_workflow_by_intruder is None


@pytest.mark.asyncio
async def test_update_workflow_definition(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="wf-2", email="wf2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = WorkflowService(db_session)
    workflow = await service.create_workflow(
        user_id=user.id, name="Original", description=None, definition=SIMPLE_DEFINITION
    )

    new_definition = {**SIMPLE_DEFINITION, "nodes": SIMPLE_DEFINITION["nodes"] + []}
    updated = await service.update_workflow(
        workflow=workflow, name="Renamed", description="Now with a description", definition=new_definition
    )

    assert updated.name == "Renamed"
    assert updated.description == "Now with a description"


@pytest.mark.asyncio
async def test_delete_workflow_removes_it(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="wf-3", email="wf3@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = WorkflowService(db_session)
    workflow = await service.create_workflow(
        user_id=user.id, name="To Delete", description=None, definition=SIMPLE_DEFINITION
    )
    await service.delete_workflow(workflow=workflow)

    fetched = await service.get_workflow(workflow_id=workflow.id, user_id=user.id)
    assert fetched is None
