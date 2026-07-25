from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    created_at: datetime


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    total_conversations: int
    total_agents: int
    total_teams: int
    total_memories: int
    total_documents: int
    total_workflows: int
    total_tool_executions: int
