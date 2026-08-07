"""
Unified global search endpoint across Agents, Chats, Documents, Memories, and Workflows.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.memory import Memory
from app.models.user import User
from app.models.workflow import Workflow

router = APIRouter(prefix="/search", tags=["Global Search"])


class SearchItem(BaseModel):
    id: int
    category: str  # "agent" | "chat" | "document" | "memory" | "workflow"
    title: str
    description: str
    path: str


class GlobalSearchResponse(BaseModel):
    results: list[SearchItem]


@router.get("", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GlobalSearchResponse:
    pattern = f"%{q.strip()}%"
    results: list[SearchItem] = []

    # 1. Search Agents
    stmt_agents = select(Agent).where(
        Agent.user_id == user.id,
        or_(Agent.name.ilike(pattern), Agent.description.ilike(pattern)),
    ).limit(5)
    res_agents = await db.execute(stmt_agents)
    for agent in res_agents.scalars().all():
        results.append(
            SearchItem(
                id=agent.id,
                category="agent",
                title=agent.name,
                description=agent.description or "AI Agent Persona",
                path="/agents",
            )
        )

    # 2. Search Conversations
    stmt_convs = select(Conversation).where(
        Conversation.user_id == user.id,
        Conversation.title.ilike(pattern),
    ).limit(5)
    res_convs = await db.execute(stmt_convs)
    for conv in res_convs.scalars().all():
        results.append(
            SearchItem(
                id=conv.id,
                category="chat",
                title=conv.title,
                description=f"Model: {conv.model}",
                path="/chat",
            )
        )

    # 3. Search Documents
    stmt_docs = select(Document).where(
        Document.user_id == user.id,
        Document.filename.ilike(pattern),
    ).limit(5)
    res_docs = await db.execute(stmt_docs)
    for doc in res_docs.scalars().all():
        results.append(
            SearchItem(
                id=doc.id,
                category="document",
                title=doc.filename,
                description=f"Type: {doc.content_type}",
                path="/documents",
            )
        )

    # 4. Search Memories
    stmt_mems = select(Memory).where(
        Memory.user_id == user.id,
        Memory.content.ilike(pattern),
    ).limit(5)
    res_mems = await db.execute(stmt_mems)
    for mem in res_mems.scalars().all():
        results.append(
            SearchItem(
                id=mem.id,
                category="memory",
                title=mem.content[:40] + ("..." if len(mem.content) > 40 else ""),
                description=f"Type: {mem.memory_type.value}",
                path="/memory",
            )
        )

    # 5. Search Workflows
    stmt_wfs = select(Workflow).where(
        Workflow.user_id == user.id,
        or_(Workflow.name.ilike(pattern), Workflow.description.ilike(pattern)),
    ).limit(5)
    res_wfs = await db.execute(stmt_wfs)
    for wf in res_wfs.scalars().all():
        results.append(
            SearchItem(
                id=wf.id,
                category="workflow",
                title=wf.name,
                description=wf.description or "Automation Pipeline",
                path=f"/workflows/{wf.id}",
            )
        )

    return GlobalSearchResponse(results=results)
