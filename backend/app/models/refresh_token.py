"""
RefreshToken model.

We don't trust bare JWT refresh tokens alone (no way to revoke a
compromised one). Instead each issued refresh token has a row here,
identified by a hash of the token (never the raw token) plus a
server-generated `jti`. Rotation: every refresh call revokes the
presented token and issues a new one, so a stolen-then-reused token
is detectable (its row will already be revoked).
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<RefreshToken jti={self.jti} user_id={self.user_id} revoked={self.revoked}>"
