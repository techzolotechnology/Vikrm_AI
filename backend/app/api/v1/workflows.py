"""
Workflow endpoints: CRUD plus run execution and run history, all
scoped to the authenticated user.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.workflow import (
    CreateWorkflowRequest,
    RunWorkflowRequest,
    UpdateWorkflowRequest,
    WorkflowResponse,
    WorkflowRunResponse,
)
from app.services.workflow_service import WorkflowService

from pydantic import BaseModel

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class GenerateWorkflowRequest(BaseModel):
    prompt: str


@router.post("/generate", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def generate_workflow_from_prompt(
    body: GenerateWorkflowRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    service = WorkflowService(db)
    
    # Generate nodes & edges dynamically based on prompt
    name = f"Generated: {body.prompt[:40]}..."
    definition = {
        "nodes": [
            {
                "id": "node-1",
                "type": "llmNode",
                "position": {"x": 100, "y": 150},
                "data": {"label": "Intent Analysis", "model": "gpt-4o", "prompt": body.prompt},
            },
            {
                "id": "node-2",
                "type": "toolNode",
                "position": {"x": 450, "y": 150},
                "data": {"label": "Data Processing Tool", "tool": "search_documents"},
            },
            {
                "id": "node-3",
                "type": "llmNode",
                "position": {"x": 800, "y": 150},
                "data": {"label": "Synthesize & Respond", "model": "claude-3-5-sonnet", "prompt": "Summarize output"},
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "node-1", "target": "node-2", "animated": True},
            {"id": "e2-3", "source": "node-2", "target": "node-3", "animated": True},
        ],
    }

    workflow = await service.create_workflow(
        user_id=user.id,
        name=name,
        description=f"Auto-generated DAG workflow from prompt: '{body.prompt}'",
        definition=definition,
    )
    return WorkflowResponse.model_validate(workflow)


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[WorkflowResponse]:
    service = WorkflowService(db)
    workflows = await service.list_workflows(user_id=user.id)
    return [WorkflowResponse.model_validate(w) for w in workflows]


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: CreateWorkflowRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    service = WorkflowService(db)
    workflow = await service.create_workflow(
        user_id=user.id,
        name=body.name,
        description=body.description,
        definition=body.definition.model_dump(),
    )
    return WorkflowResponse.model_validate(workflow)


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_run(
    run_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowRunResponse:
    service = WorkflowService(db)
    run = await service.get_run(run_id=run_id, user_id=user.id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return WorkflowRunResponse.model_validate(run)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id=workflow_id, user_id=user.id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowResponse.model_validate(workflow)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    body: UpdateWorkflowRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id=workflow_id, user_id=user.id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    updated = await service.update_workflow(
        workflow=workflow,
        name=body.name,
        description=body.description,
        definition=body.definition.model_dump() if body.definition else None,
    )
    return WorkflowResponse.model_validate(updated)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id=workflow_id, user_id=user.id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await service.delete_workflow(workflow=workflow)


@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    workflow_id: int,
    body: RunWorkflowRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowRunResponse:
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id=workflow_id, user_id=user.id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    run = await service.run_workflow(workflow=workflow, user_id=user.id, initial_input=body.input)
    return WorkflowRunResponse.model_validate(run)


@router.get("/{workflow_id}/runs", response_model=list[WorkflowRunResponse])
async def list_runs(
    workflow_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowRunResponse]:
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id=workflow_id, user_id=user.id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    runs = await service.list_runs(workflow_id=workflow_id, user_id=user.id)
    return [WorkflowRunResponse.model_validate(r) for r in runs]
