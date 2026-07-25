"""
Tests for email/password authentication flows.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.main import app


@pytest.mark.asyncio
async def test_email_register_and_login_flow(db_session: AsyncSession) -> None:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Register new user
            reg_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Test User",
                    "email": "testuser@example.com",
                    "password": "Password123!",
                },
            )
            assert reg_response.status_code == 201
            assert "Registration successful" in reg_response.json()["message"]

            # 2. Duplicate registration fails
            dup_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Test User Dup",
                    "email": "testuser@example.com",
                    "password": "Password123!",
                },
            )
            assert dup_response.status_code == 400

            # 3. Login with correct credentials
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "testuser@example.com",
                    "password": "Password123!",
                },
            )
            assert login_response.status_code == 200
            tokens = login_response.json()
            assert "access_token" in tokens
            assert "refresh_token" in tokens

            # 4. Login with wrong password
            bad_login = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "testuser@example.com",
                    "password": "WrongPassword123!",
                },
            )
            assert bad_login.status_code == 401

            # 5. Fetch profile with access token
            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            assert me_response.status_code == 200
            user_data = me_response.json()
            assert user_data["email"] == "testuser@example.com"
            assert user_data["full_name"] == "Test User"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(db_session: AsyncSession) -> None:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Register user first
            await client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Reset User",
                    "email": "reset@example.com",
                    "password": "OldPassword123!",
                },
            )

            # Request password reset
            req_response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "reset@example.com"},
            )
            assert req_response.status_code == 200

            # Invalid token reset fails
            fail_reset = await client.post(
                "/api/v1/auth/reset-password",
                json={"token": "invalid-token", "new_password": "NewPassword123!"},
            )
            assert fail_reset.status_code == 400
    finally:
        app.dependency_overrides.clear()
