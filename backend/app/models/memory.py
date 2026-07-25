"""
Memory entry model.

Canonical metadata lives in MySQL (this table); the embedding vector
lives in ChromaDB, keyed by this row's `id` (as a string) in the
`memories` collection. Storing both means the Memory Viewer UI can
list/filter/paginate via ordinary SQL without touching the vector
store, while semantic search goes through ChromaDB.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class MemoryType(str, enum.Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    CONTEXT = "context"


class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType), default=MemoryType.FACT, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Memory id={self.id} user_id={self.user_id} type={self.memory_type}>"
