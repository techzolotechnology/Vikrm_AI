from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    status: str
    char_count: int
    chunk_count: int
    error: str | None
    created_at: datetime


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=20)


class DocumentChunkResult(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    content: str
    distance: float
