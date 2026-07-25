"""
Email verification token model.

One-time tokens sent to newly registered email/password users.
Tokens expire after a configurable window. Once used, the token
is marked consumed so it cannot be replayed.
"""
import secrets
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class EmailVerificationToken(Base, TimestampMixin):
    __tablename__ = "email_verification_tokens"

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
        return f"<EmailVerificationToken user_id={self.user_id} consumed={self.consumed}>"
