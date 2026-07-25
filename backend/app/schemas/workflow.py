from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowNodeSchema(BaseModel):
    id: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] | None = None  # x/y, used by the React Flow canvas only


class WorkflowEdgeSchema(BaseModel):
    id: str | None = None
    source: str
    target: str
    branch: str | None = None  # "true" | "false", only meaningful from a condition node


class WorkflowDefinition(BaseModel):
    nodes: list[WorkflowNodeSchema]
    edges: list[WorkflowEdgeSchema]


class CreateWorkflowRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    definition: WorkflowDefinition


class UpdateWorkflowRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    definition: WorkflowDefinition | None = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    definition: dict
    created_at: datetime
    updated_at: datetime


class RunWorkflowRequest(BaseModel):
    input: str = ""


class WorkflowStepSchema(BaseModel):
    node_id: str
    node_type: str
    status: str
    input_summary: str
    output: str
    error: str | None
    started_at: str
    completed_at: str


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    status: str
    initial_input: str
    final_output: str | None
    steps: list[WorkflowStepSchema]
    error: str | None
    started_at: datetime
    completed_at: datetime | None
