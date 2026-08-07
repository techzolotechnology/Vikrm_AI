from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.services.llm.base import normalize_content_chunk


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

    @field_validator("output", mode="before")
    @classmethod
    def validate_output(cls, v: Any) -> str:
        return normalize_content_chunk(v)


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

    @field_validator("final_output", mode="before")
    @classmethod
    def validate_final_output(cls, v: Any) -> str | None:
        return normalize_content_chunk(v) if v is not None else None
