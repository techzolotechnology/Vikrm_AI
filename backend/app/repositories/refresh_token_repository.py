"""Repository for refresh_tokens — supports issuance, lookup, and revocation/rotation."""
import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: int, jti: str, raw_token: str, expires_at: datetime
    ) -> RefreshToken:
        record = RefreshToken(
            jti=jti,
            token_hash=hash_token(raw_token),
            user_id=user_id,
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def revoke(self, record: RefreshToken) -> None:
        record.revoked = True
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
            )
        )
        for record in result.scalars().all():
            record.revoked = True
        await self._session.flush()
