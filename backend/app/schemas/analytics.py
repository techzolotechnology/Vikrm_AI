from datetime import datetime

from pydantic import BaseModel


class StatusBreakdown(BaseModel):
    completed: int = 0
    failed: int = 0
    running: int = 0


class DashboardStats(BaseModel):
    total_conversations: int
    total_messages: int
    total_agents: int
    total_teams: int
    total_memories: int
    total_documents: int
    documents_ready: int
    documents_failed: int
    total_workflows: int
    workflow_runs: StatusBreakdown
    team_runs: StatusBreakdown
    total_tool_executions: int
    tool_executions_success: int
    tool_executions_failed: int


class ActivityItem(BaseModel):
    type: str  # "conversation" | "workflow_run" | "team_run" | "tool_execution" | "document"
    title: str
    status: str | None
    timestamp: datetime
