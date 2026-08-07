"""
Chat endpoints.

GET/POST /conversations                  -> list / create
GET/PATCH/DELETE /conversations/{id}     -> fetch / update (rename, pin, archive) / delete
POST /conversations/{id}/duplicate       -> duplicate conversation
GET /conversations/{id}/export           -> export conversation JSON
POST /conversations/import               -> import conversation JSON
POST /conversations/{id}/messages/stream  -> send a message, stream reply via SSE
PATCH/DELETE/BOOKMARK /conversations/{id}/messages/{message_id} -> message actions
"""
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    MessageResponse,
    SendMessageRequest,
    UpdateConversationRequest,
)
from app.services.chat_service import ChatService, ChatServiceError
from app.services.llm.base import normalize_content_chunk

logger = get_logger(__name__)
router = APIRouter(prefix="/conversations", tags=["Chat"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    is_archived: bool | None = Query(False),
    is_pinned: bool | None = Query(None),
    search: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    service = ChatService(db)
    conversations = await service.list_conversations(
        user_id=user.id,
        is_archived=is_archived,
        is_pinned=is_pinned,
        search_query=search,
    )
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


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    body: UpdateConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id=conversation_id, user_id=user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = await service.update_conversation(
        conversation=conversation,
        title=body.title,
        is_pinned=body.is_pinned,
        is_archived=body.is_archived,
        summary=body.summary,
    )
    return ConversationResponse.model_validate(updated)


@router.post("/{conversation_id}/duplicate", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id=conversation_id, user_id=user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    duplicated = await service.duplicate_conversation(conversation)
    return ConversationResponse.model_validate(duplicated)


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


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    conversation = await service.get_conversation(conversation_id=conversation_id, user_id=user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await service.export_conversation(conversation)


@router.post("/import", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def import_conversation(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    service = ChatService(db)
    imported = await service.import_conversation(user_id=user.id, data=data)
    return ConversationResponse.model_validate(imported)


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

    logger.info(
        "[stream_message] conversation=%s provider=%s model=%s user=%s",
        conversation_id, conversation.provider, conversation.model, user.id,
    )

    async def event_stream():
        try:
            async for chunk in service.stream_reply(
                conversation=conversation,
                user_content=body.content,
                attachment_ids=body.attachment_ids,
            ):
                norm_chunk = normalize_content_chunk(chunk)
                if norm_chunk:
                    yield f"data: {json.dumps({'delta': norm_chunk})}\n\n"
            yield f"data: {json.dumps({'done': True, 'title': conversation.title})}\n\n"
            yield "data: [DONE]\n\n"
        except ChatServiceError as exc:
            logger.warning("[Streaming Exception] Chat stream failed for conversation %s: %s", conversation_id, exc)
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            logger.warning("[Streaming Cancelled] Connection closed by client for conversation %s", conversation_id)
            raise
        except Exception as exc:
            logger.exception("[Streaming Exception] Unexpected error in event_stream for conversation %s", conversation_id)
            yield f"data: {json.dumps({'error': 'Internal server error. Please try again.', 'done': True})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        },
    )


@router.post("/{conversation_id}/messages/{message_id}/bookmark", response_model=MessageResponse)
async def toggle_bookmark(
    conversation_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = ChatService(db)
    msg = await service.toggle_bookmark_message(
        conversation_id=conversation_id, message_id=message_id, user_id=user.id
    )
    return MessageResponse.model_validate(msg)


@router.delete("/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    conversation_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ChatService(db)
    await service.delete_message(
        conversation_id=conversation_id, message_id=message_id, user_id=user.id
    )
