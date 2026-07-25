"""
Rate limiting middleware.

Fixed-window counter backed by Redis: `INCR` a key scoped to the
client's IP and the current minute, `EXPIRE` it on first increment,
and reject with `429` once the count exceeds
`RATE_LIMIT_REQUESTS_PER_MINUTE`. Fixed-window rather than
sliding-window/token-bucket is a deliberate simplicity tradeoff — it
allows a burst at window boundaries, an acceptable tradeoff for
protecting against sustained abuse rather than millisecond-precise
fairness.

Health/docs endpoints are exempt so uptime monitors and local API
exploration aren't rate-limited alongside real traffic.
"""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

EXEMPT_PATH_PREFIXES = ("/api/docs", "/api/redoc", "/api/openapi.json", "/api/v1/health")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, redis_client_factory) -> None:
        super().__init__(app)
        self._redis_client_factory = redis_client_factory

    async def dispatch(self, request: Request, call_next) -> Response:
        if any(request.url.path.startswith(p) for p in EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"ratelimit:{client_ip}:{window}"

        try:
            redis_client = self._redis_client_factory()
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 60)
        except Exception:
            # Redis unreachable: fail OPEN, not closed — a rate limiter
            # outage should degrade to "no rate limiting" rather than
            # "the entire API returns errors."
            return await call_next(request)

        if count > settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
