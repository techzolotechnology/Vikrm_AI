"""
JWT issuance and verification.

Two token types, both signed HS256 with JWT_SECRET_KEY:
- access token: short-lived (default 30 min), carries user id + role,
  sent as `Authorization: Bearer <token>` on every protected request.
- refresh token: longer-lived (default 7 days), carries only a `jti`
  (matched against the refresh_tokens table for revocation) — it does
  NOT carry role/permissions, so a stolen refresh token alone can't be
  used as an access token.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from pydantic import BaseModel

from app.core.config import settings


class AccessTokenPayload(BaseModel):
    sub: str  # user id, as string per JWT spec
    role: str
    type: Literal["access"] = "access"
    exp: datetime
    iat: datetime


class RefreshTokenPayload(BaseModel):
    sub: str
    jti: str
    type: Literal["refresh"] = "refresh"
    exp: datetime
    iat: datetime


def create_access_token(*, user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(*, user_id: int) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at). Caller persists jti in refresh_tokens."""
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


class TokenError(Exception):
    """Raised for any invalid/expired/malformed token."""


def decode_token(token: str, *, expected_type: Literal["access", "refresh"]) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Token is invalid") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")

    return payload


import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2$sha256$100000${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored PBKDF2-HMAC-SHA256 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 5:
            return False
        algorithm, hash_name, iterations_str, salt_hex, key_hex = parts
        if algorithm != "pbkdf2" or hash_name != "sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


