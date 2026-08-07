"""
Agent model with versioning support.
"""
import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_color: Mapped[str] = mapped_column(String(20), default="#7C3AED", nullable=False)

    # Behavior
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model settings
    provider: Mapped[str] = mapped_column(String(50), default="ollama", nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="llama3.2", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus), default=AgentStatus.ACTIVE, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id} name={self.name!r} user_id={self.user_id} version={self.version}>"
