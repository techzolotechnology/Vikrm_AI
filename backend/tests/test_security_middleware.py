"""
Tests security_headers.py and rate_limit.py against a real (in-memory,
via fakeredis) Redis-compatible client — not mocked responses. The
rate limiter's actual counting/expiry/429 logic is exercised for real.
"""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.responses import PlainTextResponse

from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware


def _build_test_app(*, redis_factory) -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/echo")
    async def echo():
        return PlainTextResponse("ok")

    @app.get("/api/v1/health")
    async def health():
        return PlainTextResponse("healthy")

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, redis_client_factory=redis_factory)
    return app


@pytest.mark.asyncio
async def test_security_headers_present_on_every_response() -> None:
    import fakeredis.aioredis

    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app = _build_test_app(redis_factory=lambda: fake_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/echo")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    # HSTS only applies in production; default test environment is "development".
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_rate_limit_allows_requests_under_the_limit() -> None:
    import fakeredis.aioredis

    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app = _build_test_app(redis_factory=lambda: fake_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            response = await client.get("/api/v1/echo")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_exceeding_threshold(monkeypatch) -> None:
    import fakeredis.aioredis

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS_PER_MINUTE", 3)
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app = _build_test_app(redis_factory=lambda: fake_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        statuses = [(await client.get("/api/v1/echo")).status_code for _ in range(5)]

    assert statuses[:3] == [200, 200, 200]
    assert statuses[3:] == [429, 429]


@pytest.mark.asyncio
async def test_rate_limit_returns_retry_after_header(monkeypatch) -> None:
    import fakeredis.aioredis

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS_PER_MINUTE", 1)
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app = _build_test_app(redis_factory=lambda: fake_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/api/v1/echo")
        blocked = await client.get("/api/v1/echo")

    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"


@pytest.mark.asyncio
async def test_health_endpoint_is_exempt_from_rate_limiting(monkeypatch) -> None:
    import fakeredis.aioredis

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS_PER_MINUTE", 1)
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app = _build_test_app(redis_factory=lambda: fake_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        statuses = [(await client.get("/api/v1/health")).status_code for _ in range(10)]

    assert all(s == 200 for s in statuses)


@pytest.mark.asyncio
async def test_rate_limiter_fails_open_when_redis_unreachable() -> None:
    """An unreachable Redis must never take the whole API down."""

    def broken_redis_factory():
        class BrokenClient:
            async def incr(self, key):
                raise ConnectionError("simulated redis outage")

        return BrokenClient()

    app = _build_test_app(redis_factory=broken_redis_factory)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/echo")

    assert response.status_code == 200


def test_production_with_default_secret_refuses_to_start() -> None:
    from app.core.config import Settings

    test_settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="change-me-in-production")
    with pytest.raises(RuntimeError, match="Refusing to start"):
        test_settings.validate_production_safety()


def test_production_with_real_secret_starts_fine() -> None:
    from app.core.config import Settings

    test_settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="a-real-randomly-generated-secret")
    test_settings.validate_production_safety()  # must not raise


def test_development_with_default_secret_is_allowed() -> None:
    from app.core.config import Settings

    test_settings = Settings(ENVIRONMENT="development", JWT_SECRET_KEY="change-me-in-production")
    test_settings.validate_production_safety()  # must not raise — dev is fine with a placeholder
