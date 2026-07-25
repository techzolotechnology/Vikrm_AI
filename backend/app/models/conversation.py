"""
Conversation model.

A conversation belongs to one user and holds an ordered list of
messages. `provider`/`model` are stored per-conversation, seeded from
the linked `agent` at creation time if one is chosen (Milestone 4);
a conversation can also exist without an agent, using ad-hoc
provider/model settings directly (Milestone 3 behavior, still supported).
"""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.message import Message


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="ollama", nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="llama3.2", nullable=False)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user_id={self.user_id} title={self.title!r}>"
