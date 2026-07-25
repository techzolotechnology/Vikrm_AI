"""
Analytics service.

Every number here comes from an actual COUNT/GROUP BY query against
the tables each prior milestone created — nothing is estimated or
hardcoded. This is deliberately a thin, read-only aggregation layer:
it doesn't own any data, just summarizes what `ChatService`,
`WorkflowService`, `OrchestrationService`, `MemoryService`,
`RagService`, and `ToolExecutionService` have already persisted.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.agent_team import AgentTeam, AgentTeamRun, TeamRunStatus
from app.models.conversation import Conversation
from app.models.document import Document, DocumentStatus
from app.models.memory import Memory
from app.models.message import Message
from app.models.tool_execution import ToolExecution, ToolExecutionStatus
from app.models.workflow import Workflow, WorkflowRun, WorkflowRunStatus
from app.schemas.analytics import ActivityItem, DashboardStats, StatusBreakdown


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _count(self, model, *filters) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(model).where(*filters)
        )
        return result.scalar_one()

    async def get_dashboard_stats(self, *, user_id: int) -> DashboardStats:
        total_conversations = await self._count(Conversation, Conversation.user_id == user_id)

        message_count_result = await self._session.execute(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
        )
        total_messages = message_count_result.scalar_one()

        total_agents = await self._count(Agent, Agent.user_id == user_id)
        total_teams = await self._count(AgentTeam, AgentTeam.user_id == user_id)
        total_memories = await self._count(Memory, Memory.user_id == user_id)

        total_documents = await self._count(Document, Document.user_id == user_id)
        documents_ready = await self._count(
            Document, Document.user_id == user_id, Document.status == DocumentStatus.READY
        )
        documents_failed = await self._count(
            Document, Document.user_id == user_id, Document.status == DocumentStatus.FAILED
        )

        total_workflows = await self._count(Workflow, Workflow.user_id == user_id)

        workflow_runs = StatusBreakdown(
            completed=await self._count(
                WorkflowRun,
                WorkflowRun.user_id == user_id,
                WorkflowRun.status == WorkflowRunStatus.COMPLETED,
            ),
            failed=await self._count(
                WorkflowRun,
                WorkflowRun.user_id == user_id,
                WorkflowRun.status == WorkflowRunStatus.FAILED,
            ),
            running=await self._count(
                WorkflowRun,
                WorkflowRun.user_id == user_id,
                WorkflowRun.status == WorkflowRunStatus.RUNNING,
            ),
        )

        team_runs = StatusBreakdown(
            completed=await self._count(
                AgentTeamRun,
                AgentTeamRun.user_id == user_id,
                AgentTeamRun.status == TeamRunStatus.COMPLETED,
            ),
            failed=await self._count(
                AgentTeamRun,
                AgentTeamRun.user_id == user_id,
                AgentTeamRun.status == TeamRunStatus.FAILED,
            ),
            running=await self._count(
                AgentTeamRun,
                AgentTeamRun.user_id == user_id,
                AgentTeamRun.status == TeamRunStatus.RUNNING,
            ),
        )

        total_tool_executions = await self._count(ToolExecution, ToolExecution.user_id == user_id)
        tool_executions_success = await self._count(
            ToolExecution,
            ToolExecution.user_id == user_id,
            ToolExecution.status == ToolExecutionStatus.SUCCESS,
        )
        tool_executions_failed = await self._count(
            ToolExecution,
            ToolExecution.user_id == user_id,
            ToolExecution.status == ToolExecutionStatus.FAILED,
        )

        return DashboardStats(
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_agents=total_agents,
            total_teams=total_teams,
            total_memories=total_memories,
            total_documents=total_documents,
            documents_ready=documents_ready,
            documents_failed=documents_failed,
            total_workflows=total_workflows,
            workflow_runs=workflow_runs,
            team_runs=team_runs,
            total_tool_executions=total_tool_executions,
            tool_executions_success=tool_executions_success,
            tool_executions_failed=tool_executions_failed,
        )

    async def get_recent_activity(self, *, user_id: int, limit: int = 20) -> list[ActivityItem]:
        items: list[ActivityItem] = []

        conversations = await self._session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(limit)
        )
        for c in conversations.scalars().all():
            items.append(
                ActivityItem(type="conversation", title=c.title, status=None, timestamp=c.updated_at)
            )

        workflow_runs = await self._session.execute(
            select(WorkflowRun, Workflow.name)
            .join(Workflow, WorkflowRun.workflow_id == Workflow.id)
            .where(WorkflowRun.user_id == user_id)
            .order_by(WorkflowRun.started_at.desc(), WorkflowRun.id.desc())
            .limit(limit)
        )
        for run, workflow_name in workflow_runs.all():
            items.append(
                ActivityItem(
                    type="workflow_run",
                    title=f"Workflow: {workflow_name}",
                    status=run.status.value,
                    timestamp=run.started_at,
                )
            )

        team_runs = await self._session.execute(
            select(AgentTeamRun, AgentTeam.name)
            .join(AgentTeam, AgentTeamRun.team_id == AgentTeam.id)
            .where(AgentTeamRun.user_id == user_id)
            .order_by(AgentTeamRun.started_at.desc(), AgentTeamRun.id.desc())
            .limit(limit)
        )
        for run, team_name in team_runs.all():
            items.append(
                ActivityItem(
                    type="team_run",
                    title=f"Team: {team_name}",
                    status=run.status.value,
                    timestamp=run.started_at,
                )
            )

        documents = await self._session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc(), Document.id.desc())
            .limit(limit)
        )
        for d in documents.scalars().all():
            items.append(
                ActivityItem(
                    type="document",
                    title=f"Uploaded: {d.filename}",
                    status=d.status.value,
                    timestamp=d.created_at,
                )
            )

        items.sort(key=lambda i: i.timestamp, reverse=True)
        return items[:limit]
