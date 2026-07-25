"""
Confirms the new admin endpoints are actually protected at the API
layer, not just callable-but-unsafe if a router mistake ever bypassed
the service-level checks. Mirrors the pattern from
test_auth_endpoints.py's test_users_list_requires_admin_role.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_admin_users_list_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_update_user_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch("/api/v1/admin/users/1", json={"role": "admin"})
    assert response.status_code == 401
