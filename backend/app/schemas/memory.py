from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateMemoryRequest(BaseModel):
    content: str = Field(min_length=1)
    memory_type: str = "fact"
    agent_id: int | None = None


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    memory_type: str
    agent_id: int | None
    created_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


class MemorySearchResult(BaseModel):
    memory: MemoryResponse
    distance: float
