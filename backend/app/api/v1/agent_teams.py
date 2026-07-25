"""
Multi-agent team endpoints: CRUD plus run execution and run history,
scoped to the authenticated user.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.agent_team import (
    CreateTeamRequest,
    RunTeamRequest,
    TeamResponse,
    TeamRunResponse,
)
from app.services.orchestration_service import OrchestrationError, OrchestrationService

router = APIRouter(prefix="/agent-teams", tags=["Multi-Agent Orchestration"])


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[TeamResponse]:
    service = OrchestrationService(db)
    teams = await service.list_teams(user_id=user.id)
    return [TeamResponse.model_validate(t) for t in teams]


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: CreateTeamRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    service = OrchestrationService(db)
    try:
        team = await service.create_team(
            user_id=user.id,
            name=body.name,
            description=body.description,
            manager_agent_id=body.manager_agent_id,
            member_agent_ids=body.member_agent_ids,
        )
    except OrchestrationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TeamResponse.model_validate(team)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    service = OrchestrationService(db)
    team = await service.get_team(team_id=team_id, user_id=user.id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.model_validate(team)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = OrchestrationService(db)
    team = await service.get_team(team_id=team_id, user_id=user.id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    await service.delete_team(team=team)


@router.post("/{team_id}/run", response_model=TeamRunResponse)
async def run_team(
    team_id: int,
    body: RunTeamRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamRunResponse:
    service = OrchestrationService(db)
    team = await service.get_team(team_id=team_id, user_id=user.id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    try:
        run = await service.run_team(team=team, user_id=user.id, task=body.task)
    except OrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TeamRunResponse.model_validate(run)


@router.get("/{team_id}/runs", response_model=list[TeamRunResponse])
async def list_runs(
    team_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeamRunResponse]:
    service = OrchestrationService(db)
    team = await service.get_team(team_id=team_id, user_id=user.id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    runs = await service.list_runs(team_id=team_id, user_id=user.id)
    return [TeamRunResponse.model_validate(r) for r in runs]
