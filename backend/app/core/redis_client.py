"""
Redis connection management.

A single connection pool is created at import time and reused across
requests. `check_redis_connection` backs the readiness probe; later
milestones (Celery broker, chat pub/sub, rate limiting) reuse `redis_pool`.
"""
import redis.asyncio as redis

from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=20,
)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)


async def check_redis_connection() -> bool:
    try:
        client = get_redis()
        pong = await client.ping()
        await client.aclose()
        return bool(pong)
    except Exception:
        return False
