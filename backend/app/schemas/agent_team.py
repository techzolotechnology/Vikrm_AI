from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    manager_agent_id: int
    member_agent_ids: list[int] = Field(min_length=1)


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    manager_agent_id: int
    member_agent_ids: list[int]
    created_at: datetime
    updated_at: datetime


class RunTeamRequest(BaseModel):
    task: str = Field(min_length=1)


class TeamRunStepSchema(BaseModel):
    agent_name: str
    subtask: str
    output: str
    status: str
    error: str | None


class TeamRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    task: str
    status: str
    plan: list[dict]
    steps: list[TeamRunStepSchema]
    final_output: str | None
    error: str | None
    started_at: datetime
    completed_at: datetime | None
