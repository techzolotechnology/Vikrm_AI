"""
Auth service.

Verifies Google ID tokens using google-auth's cryptographic verification
against Google's published public keys (fetched and cached internally
by the library) — this is real signature + audience + issuer
verification, not a trust-the-client shortcut. On first sign-in we
create the user; on subsequent sign-ins we look them up by
`google_sub` (not email, since email can change).
"""
from datetime import datetime, timedelta, timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import AuthProvider, User, UserRole
from app.repositories.refresh_token_repository import RefreshTokenRepository, hash_token
from app.repositories.user_repository import UserRepository


from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthError(Exception):
    """Raised for any authentication failure the API layer should turn into 401."""


class GoogleTokenInfo:
    def __init__(self, sub: str, email: str, name: str | None, picture: str | None) -> None:
        self.sub = sub
        self.email = email
        self.name = name
        self.picture = picture


def verify_google_id_token(raw_id_token: str) -> GoogleTokenInfo:
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("[Auth Service] Google OAuth failed: GOOGLE_CLIENT_ID is not configured on the server")
        raise AuthError("GOOGLE_CLIENT_ID is not configured on the server")

    logger.info("[Auth Service] Verifying Google ID token against audience")
    try:
        payload = google_id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,  # Tolerate Docker/WSL2 clock drift
        )
    except Exception as exc:
        logger.warning("[Auth Service] Google OAuth token verification failed: %s", exc)
        raise AuthError(f"Invalid Google ID token: {exc}") from exc

    issuer = payload.get("iss")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        logger.warning("[Auth Service] Google ID token has invalid issuer: %s", issuer)
        raise AuthError("Invalid token issuer")

    if not payload.get("email_verified", False):
        logger.warning("[Auth Service] Google account email is not verified: %s", payload.get("email"))
        raise AuthError("Google account email is not verified")

    logger.info("[Auth Service] Google token verified successfully: sub=%s, email=%s", payload["sub"], payload.get("email"))
    return GoogleTokenInfo(
        sub=payload["sub"],
        email=payload["email"],
        name=payload.get("name"),
        picture=payload.get("picture"),
    )


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._refresh_tokens = RefreshTokenRepository(session)

    async def authenticate_with_google(self, raw_id_token: str) -> tuple[User, str, str]:
        """Verifies the Google ID token, finds-or-creates the user, and
        issues a fresh access/refresh token pair. Returns (user, access, refresh)."""
        info = verify_google_id_token(raw_id_token)

        logger.info("[Auth Service] Looking up user by google_sub=%s", info.sub)
        user = await self._users.get_by_google_sub(info.sub)
        if user is None:
            logger.info("[Auth Service] User not found by google_sub. Checking email=%s", info.email)
            existing_any = await self._users.get_by_email(info.email)
            if existing_any is not None:
                logger.info(
                    "[Auth Service] Linking existing email user %s (id=%s) to Google account (sub=%s)",
                    info.email,
                    existing_any.id,
                    info.sub,
                )
                user = existing_any
                user.google_sub = info.sub
                if info.picture and not user.avatar_url:
                    user.avatar_url = info.picture
                if info.name and not user.full_name:
                    user.full_name = info.name
            else:
                user_count = await self._users.count()
                role = UserRole.ADMIN if user_count == 0 else UserRole.USER
                logger.info("[Auth Service] Creating new user via Google OAuth: %s (role=%s)", info.email, role)
                user = User(
                    google_sub=info.sub,
                    email=info.email.lower().strip(),
                    full_name=info.name,
                    avatar_url=info.picture,
                    auth_provider=AuthProvider.GOOGLE,
                    email_verified=True,
                    role=role,
                )
                self._session.add(user)
                await self._session.flush()
        else:
            logger.info("[Auth Service] User found by google_sub: user_id=%s (%s)", user.id, user.email)
            user = await self._users.update_profile(
                user, full_name=info.name, avatar_url=info.picture
            )

        logger.info("[Auth Service] Generating Vikrm JWT token pair for user_id=%s", user.id)
        access_token, refresh_token = await self._issue_token_pair(user)
        await self._session.commit()
        logger.info("[Auth Service] Google OAuth authentication process complete for user_id=%s", user.id)
        return user, access_token, refresh_token



    async def register_with_email(
        self, full_name: str, email: str, password: str
    ) -> tuple[User, str]:
        """Registers a new user with email/password. Creates email verification token."""
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AuthError("An account with this email already exists")

        user_count = await self._users.count()
        role = UserRole.ADMIN if user_count == 0 else UserRole.USER
        hashed_pw = hash_password(password)

        user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            auth_provider=AuthProvider.EMAIL,
            password_hash=hashed_pw,
            email_verified=True,  # Local auto-verify for smooth self-hosted onboarding
            role=role,
        )
        self._session.add(user)
        await self._session.flush()

        raw_token = EmailVerificationToken.generate_token()
        token_obj = EmailVerificationToken(
            user_id=user.id,
            token=raw_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self._session.add(token_obj)
        await self._session.commit()
        return user, raw_token

    async def login_with_email(self, email: str, password: str) -> tuple[User, str, str]:
        """Authenticates user with email and password, returning (user, access, refresh)."""
        user = await self._users.get_by_email(email.lower().strip())
        if user is None or not user.password_hash:
            raise AuthError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")

        if not user.is_active:
            raise AuthError("User account is inactive")

        access_token, refresh_token = await self._issue_token_pair(user)
        await self._session.commit()
        return user, access_token, refresh_token

    async def verify_email(self, token: str) -> User:
        """Verifies an email using a verification token."""
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token == token,
            EmailVerificationToken.consumed == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            raise AuthError("Invalid or expired verification token")

        if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise AuthError("Verification token has expired")

        user = await self._users.get_by_id(record.user_id)
        if user is None:
            raise AuthError("User not found")

        record.consumed = True
        user.email_verified = True
        await self._session.commit()
        return user

    async def request_password_reset(self, email: str) -> str | None:
        """Creates a password reset token for user if found."""
        user = await self._users.get_by_email(email.lower().strip())
        if user is None or user.auth_provider != AuthProvider.EMAIL:
            return None  # Idempotent response to prevent account enumeration

        raw_token = PasswordResetToken.generate_token()
        token_obj = PasswordResetToken(
            user_id=user.id,
            token=raw_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self._session.add(token_obj)
        await self._session.commit()
        return raw_token

    async def reset_password(self, token: str, new_password: str) -> User:
        """Resets a user's password using a reset token."""
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.consumed == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            raise AuthError("Invalid or expired password reset token")

        if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise AuthError("Password reset token has expired")

        user = await self._users.get_by_id(record.user_id)
        if user is None:
            raise AuthError("User not found")

        record.consumed = True
        user.password_hash = hash_password(new_password)
        await self._session.commit()
        return user

    async def refresh(self, raw_refresh_token: str) -> tuple[User, str, str]:
        """Validates + rotates a refresh token. Raises AuthError on any
        invalid, expired, revoked, or reused token."""
        try:
            payload = decode_token(raw_refresh_token, expected_type="refresh")
        except TokenError as exc:
            raise AuthError(str(exc)) from exc

        record = await self._refresh_tokens.get_by_jti(payload["jti"])
        if record is None:
            raise AuthError("Refresh token not recognized")
        if record.revoked:
            await self._refresh_tokens.revoke_all_for_user(record.user_id)
            await self._session.commit()
            raise AuthError("Refresh token has already been used; all sessions revoked")
        if record.token_hash != hash_token(raw_refresh_token):
            raise AuthError("Refresh token does not match stored record")
        if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise AuthError("Refresh token has expired")

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise AuthError("User account is inactive or no longer exists")

        await self._refresh_tokens.revoke(record)
        access_token, refresh_token = await self._issue_token_pair(user)
        await self._session.commit()
        return user, access_token, refresh_token

    async def _issue_token_pair(self, user: User) -> tuple[str, str]:
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token, jti, expires_at = create_refresh_token(user_id=user.id)
        await self._refresh_tokens.create(
            user_id=user.id, jti=jti, raw_token=refresh_token, expires_at=expires_at
        )
        return access_token, refresh_token

