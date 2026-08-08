from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    avatar_color: str = "#7C3AED"
    instructions: str | None = None
    goal: str | None = None
    personality: str | None = None
    provider: str = "ollama"
    model: str = "qwen3:8b"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32768)


class CreateAgentRequest(AgentBase):
    pass


class UpdateAgentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    avatar_color: str | None = None
    instructions: str | None = None
    goal: str | None = None
    personality: str | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=32768)
    status: str | None = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime
