"""
Password reset token model.

Short-lived, one-time tokens for email/password users to reset their
password. Tokens are invalidated after use or expiry.
"""
import secrets
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class PasswordResetToken(Base, TimestampMixin):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(48)

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id} consumed={self.consumed}>"
