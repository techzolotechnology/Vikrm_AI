"""
Tests for the health/readiness/version endpoints.

Run with: pytest (inside the backend container or a local venv with
requirements installed and MySQL/Redis reachable per .env).
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "Vikrm"


@pytest.mark.asyncio
async def test_version_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/version")
    assert response.status_code == 200
    body = response.json()
    assert "environment" in body


@pytest.mark.asyncio
async def test_readiness_endpoint_shape() -> None:
    """Readiness may report degraded if DB/Redis aren't reachable in this
    environment, but the response contract itself must always hold."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ready", "degraded")
    assert body["database"] in ("up", "down")
    assert body["redis"] in ("up", "down")
