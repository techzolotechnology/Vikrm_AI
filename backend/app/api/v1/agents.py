"""
Agent management endpoints. All scoped to the authenticated user —
agents are private until a Marketplace/sharing feature (a later
milestone) introduces a visibility column.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.agent import AgentResponse, CreateAgentRequest, UpdateAgentRequest
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentResponse]:
    service = AgentService(db)
    agents = await service.list_agents(user_id=user.id, include_archived=include_archived)
    return [AgentResponse.model_validate(a) for a in agents]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: CreateAgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    service = AgentService(db)
    agent = await service.create_agent(user_id=user.id, data=body.model_dump())
    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    service = AgentService(db)
    agent = await service.get_agent(agent_id=agent_id, user_id=user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    body: UpdateAgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    service = AgentService(db)
    agent = await service.get_agent(agent_id=agent_id, user_id=user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    updated = await service.update_agent(
        agent=agent, data=body.model_dump(exclude_unset=True)
    )
    return AgentResponse.model_validate(updated)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AgentService(db)
    agent = await service.get_agent(agent_id=agent_id, user_id=user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    await service.delete_agent(agent=agent)


@router.post("/{agent_id}/duplicate", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    service = AgentService(db)
    agent = await service.get_agent(agent_id=agent_id, user_id=user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    duplicated = await service.duplicate_agent(agent=agent, user_id=user.id)
    return AgentResponse.model_validate(duplicated)

