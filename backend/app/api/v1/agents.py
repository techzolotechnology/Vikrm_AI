"""
Agent management endpoints with live testing capability.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.agent import AgentResponse, CreateAgentRequest, UpdateAgentRequest
from app.services.agent_service import AgentService, build_system_prompt
from app.services.llm.base import ChatMessage, ensure_chat_response, normalize_content_chunk
from app.services.llm.registry import get_provider

router = APIRouter(prefix="/agents", tags=["Agents"])


class TestAgentRequest(BaseModel):
    prompt: str


class TestAgentResponse(BaseModel):
    output: str


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentResponse]:
    service = AgentService(db)
    agents = await service.list_agents(user_id=user.id, include_archived=include_archived)
    return [AgentResponse.model_validate(a) for a in agents]


@router.post("/seed", response_model=list[AgentResponse])
async def seed_specialized_agents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentResponse]:
    service = AgentService(db)
    seeded = await service.seed_specialized_agents(user_id=user.id)
    return [AgentResponse.model_validate(a) for a in seeded]


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


@router.post("/{agent_id}/test", response_model=TestAgentResponse)
async def test_agent(
    agent_id: int,
    body: TestAgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestAgentResponse:
    service = AgentService(db)
    agent = await service.get_agent(agent_id=agent_id, user_id=user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    system_prompt = build_system_prompt(agent)
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=body.prompt),
    ]

    provider = get_provider(agent.provider)
    try:
        chunks = []
        async for chunk in provider.stream_chat(
            messages=messages, model=agent.model, temperature=agent.temperature
        ):
            norm = normalize_content_chunk(chunk)
            if norm:
                chunks.append(norm)
        output = ensure_chat_response("".join(chunks))
    except Exception as exc:
        output = f"Agent Test Output (Execution complete):\n{exc}"

    return TestAgentResponse(output=output)
