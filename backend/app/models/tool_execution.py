"""
ToolExecution model.

Every tool invocation — whether triggered from a workflow's `tool`
node or a direct `/tools/{name}/execute` call — is logged here. This
is what a future dashboard's "tool usage" panel reads from, and it's
also just useful for a user to answer "what did my Python executor
actually run and what did it output" after the fact.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ToolExecutionStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ToolExecution(Base, TimestampMixin):
    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ToolExecutionStatus] = mapped_column(Enum(ToolExecutionStatus), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<ToolExecution id={self.id} tool={self.tool_name!r} status={self.status}>"
