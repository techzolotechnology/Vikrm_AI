"""
User repository.

Owns all direct SQLAlchemy queries against the `users` table. Services
call this instead of touching the session/ORM directly — this is the
seam that would let us swap storage later without touching business logic.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuthProvider, User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_google_sub(self, google_sub: str) -> User | None:
        result = await self._session.execute(select(User).where(User.google_sub == google_sub))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        google_sub: str | None = None,
        full_name: str | None = None,
        avatar_url: str | None = None,
        password_hash: str | None = None,
        auth_provider: AuthProvider = AuthProvider.GOOGLE,
        role: UserRole = UserRole.USER,
    ) -> User:
        user = User(
            google_sub=google_sub,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            password_hash=password_hash,
            auth_provider=auth_provider,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user


    async def update_profile(
        self, user: User, *, full_name: str | None, avatar_url: str | None
    ) -> User:
        user.full_name = full_name
        user.avatar_url = avatar_url
        await self._session.flush()
        await self._session.refresh(user)
        return user
