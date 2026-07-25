"""Unit tests for token creation/verification — the part of auth that
doesn't require a live database or a real Google token."""
import pytest

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_access_token_roundtrip() -> None:
    token = create_access_token(user_id=42, role="user")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "42"
    assert payload["role"] == "user"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip() -> None:
    token, jti, expires_at = create_refresh_token(user_id=7)
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == "7"
    assert payload["jti"] == jti
    assert payload["type"] == "refresh"
    assert expires_at.tzinfo is not None


def test_wrong_token_type_rejected() -> None:
    access = create_access_token(user_id=1, role="admin")
    with pytest.raises(TokenError):
        decode_token(access, expected_type="refresh")


def test_tampered_token_rejected() -> None:
    token = create_access_token(user_id=1, role="user")
    # Flip a character in the middle of the payload segment rather than
    # the very last character of the signature: the last base64url char
    # of a 256-bit HMAC digest encodes some unused padding bits, so
    # flipping it can occasionally leave the decoded signature bytes
    # unchanged (a flaky false-negative, not a real security issue).
    # Corrupting the payload segment always invalidates the signature.
    header, payload, signature = token.split(".")
    mid = len(payload) // 2
    tampered_char = "A" if payload[mid] != "A" else "B"
    tampered_payload = payload[:mid] + tampered_char + payload[mid + 1 :]
    tampered = f"{header}.{tampered_payload}.{signature}"
    with pytest.raises(TokenError):
        decode_token(tampered, expected_type="access")


def test_garbage_token_rejected() -> None:
    with pytest.raises(TokenError):
        decode_token("not-a-real-token", expected_type="access")


def test_password_hashing() -> None:
    from app.core.security import hash_password, verify_password

    pw = "SuperSecretPassword123!"
    hashed = hash_password(pw)
    assert hashed.startswith("pbkdf2$sha256$100000$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


