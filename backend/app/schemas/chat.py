from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator
from app.services.llm.base import normalize_content_chunk


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    message_id: int | None
    filename: str
    file_type: str
    file_size: int
    file_path: str
    extracted_text: str | None = None
    created_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    error: str | None = None
    is_bookmarked: bool = False
    edited_at: datetime | None = None
    created_at: datetime
    attachments: list[AttachmentResponse] = []

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: Any) -> str:
        return normalize_content_chunk(v)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    provider: str
    model: str
    agent_id: int | None = None
    is_pinned: bool = False
    is_archived: bool = False
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    attachments: list[AttachmentResponse] = []


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


class CreateConversationRequest(BaseModel):
    title: str | None = None
    provider: str | None = None
    model: str | None = None
    agent_id: int | None = None


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None
    is_archived: bool | None = None
    summary: str | None = None


class SendMessageRequest(BaseModel):
    content: str
    attachment_ids: list[int] | None = None


class EditMessageRequest(BaseModel):
    content: str
