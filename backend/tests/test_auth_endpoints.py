"""
Tests for auth-guarded endpoint behavior that don't require a live DB:
missing/invalid bearer tokens must be rejected before any DB call happens.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_me_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_garbage_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_users_list_requires_admin_role() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cors_preflight_options() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/api/v1/auth/google",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_google_oauth_endpoint_returns_401_on_invalid_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/google",
            json={"id_token": "invalid-google-token"},
            headers={"Origin": "http://localhost:5173"},
        )
    assert response.status_code == 401
    assert "detail" in response.json()

