"""
Multi-agent orchestration models.

A team is a manager agent plus a roster of member agents. Unlike a
Workflow (Milestone 7), which executes a fixed, pre-drawn graph, a
team's execution path is decided dynamically at run time by the
manager agent — the same task can produce a different delegation plan
each time depending on what the manager decides is needed.
"""
import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class TeamRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTeam(Base, TimestampMixin):
    __tablename__ = "agent_teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    member_agent_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    def __repr__(self) -> str:
        return f"<AgentTeam id={self.id} name={self.name!r}>"


class AgentTeamRun(Base, TimestampMixin):
    __tablename__ = "agent_team_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("agent_teams.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TeamRunStatus] = mapped_column(
        Enum(TeamRunStatus), default=TeamRunStatus.RUNNING, nullable=False
    )
    plan: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    final_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentTeamRun id={self.id} team_id={self.team_id} status={self.status}>"
