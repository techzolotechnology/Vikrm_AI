from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExecuteToolRequest(BaseModel):
    input: str = Field(min_length=1)


class ToolExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_name: str
    input_text: str
    output_text: str | None
    status: str
    error: str | None
    duration_ms: int
    created_at: datetime
