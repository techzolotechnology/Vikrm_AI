from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    error: str | None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    provider: str
    model: str
    agent_id: int | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class CreateConversationRequest(BaseModel):
    title: str | None = None
    provider: str | None = None
    model: str | None = None
    agent_id: int | None = None


class SendMessageRequest(BaseModel):
    content: str
