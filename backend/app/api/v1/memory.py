"""
Memory endpoints: CRUD plus a semantic search endpoint used both by
the frontend Memory Viewer and internally by ChatService to surface
relevant memories during a conversation.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.memory import MemoryType
from app.models.user import User
from app.schemas.memory import (
    CreateMemoryRequest,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResult,
)
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["Memory"])


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[MemoryResponse]:
    service = MemoryService(db)
    memories = await service.list_memories(user_id=user.id)
    return [MemoryResponse.model_validate(m) for m in memories]


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: CreateMemoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    try:
        memory_type = MemoryType(body.memory_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid memory_type. Must be one of: {[t.value for t in MemoryType]}",
        ) from exc

    service = MemoryService(db)
    memory = await service.create_memory(
        user_id=user.id, content=body.content, memory_type=memory_type, agent_id=body.agent_id
    )
    return MemoryResponse.model_validate(memory)


@router.post("/search", response_model=list[MemorySearchResult])
async def search_memories(
    body: MemorySearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemorySearchResult]:
    service = MemoryService(db)
    results = await service.search_memories(user_id=user.id, query=body.query, top_k=body.top_k)
    return [
        MemorySearchResult(memory=MemoryResponse.model_validate(memory), distance=distance)
        for memory, distance in results
    ]


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = MemoryService(db)
    memory = await service.get_memory(memory_id=memory_id, user_id=user.id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    await service.delete_memory(memory=memory)
