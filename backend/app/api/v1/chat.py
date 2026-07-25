"""
Chat endpoints.

GET/POST /conversations                  -> list / create
GET/DELETE /conversations/{id}            -> fetch with full message history / delete
POST /conversations/{id}/messages/stream  -> send a message, stream the reply via SSE

Streaming uses Server-Sent Events (`text/event-stream`) rather than a
raw chunked response so the browser's native EventSource-compatible
fetch-stream parsing on the frontend can consume it with reconnection
semantics understood, and so proxies/load balancers treat it correctly.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.chat import (
    ConversationDetailResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendMessageRequest,
)
from app.services.chat_service import ChatService, ChatServiceError

logger = get_logger(__name__)
router = APIRouter(prefix="/conversations", tags=["Chat"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ConversationResponse]:
    service = ChatService(db)
    conversations = await service.list_conversations(user_id=user.id)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    service = ChatService(db)
    try:
        conversation = await service.create_conversation(
            user_id=user.id,
            title=body.title,
            provider=body.provider,
            model=body.model,
            agent_id=body.agent_id,
        )
    except ChatServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id=conversation_id, user_id=user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetailResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id=conversation_id, user_id=user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await service.delete_conversation(conversation)


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id=conversation_id, user_id=user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def event_stream():
        try:
            async for chunk in service.stream_reply(
                conversation=conversation, user_content=body.content
            ):
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except ChatServiceError as exc:
            logger.warning("Chat stream failed for conversation %s: %s", conversation_id, exc)
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for real-time streaming
        },
    )
