"""
User model.

Supports two authentication providers:
- Google OAuth 2.0 (original, stable): identified by `google_sub`
- Email/password (added): identified by hashed password with bcrypt

`google_sub` is Google's stable, unique subject identifier for the
account and is what we authenticate against for Google users, not email
(emails can change). For email/password users, `google_sub` is NULL.
"""
import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class AuthProvider(str, enum.Enum):
    GOOGLE = "google"
    EMAIL = "email"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Google OAuth fields (nullable for email/password users)
    google_sub: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    # Core identity
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Auth provider and credentials
    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider), default=AuthProvider.GOOGLE, nullable=False
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Account state
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role} provider={self.auth_provider}>"
