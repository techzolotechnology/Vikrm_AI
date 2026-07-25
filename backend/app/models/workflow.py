"""
Workflow models.

`Workflow.definition` stores the full node/edge graph as JSON — this
is the same shape the React Flow builder (Milestone 8) edits directly,
so there's no translation layer between "what the UI drew" and "what
the engine executes." `WorkflowRun.steps` stores the per-node
execution timeline (also JSON) so a run can be replayed/inspected
without a separate steps table — reasonable for the step counts a
visual workflow builder produces; a very high-volume workflow system
would likely want steps normalized into their own table instead.
"""
import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class WorkflowRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"<Workflow id={self.id} name={self.name!r}>"


class WorkflowRun(Base, TimestampMixin):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[WorkflowRunStatus] = mapped_column(
        Enum(WorkflowRunStatus), default=WorkflowRunStatus.RUNNING, nullable=False
    )
    initial_input: Mapped[str] = mapped_column(Text, nullable=False)
    final_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<WorkflowRun id={self.id} workflow_id={self.workflow_id} status={self.status}>"
