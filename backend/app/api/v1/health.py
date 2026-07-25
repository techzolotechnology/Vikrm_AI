"""
Health and readiness endpoints.

/health        -> liveness: is the process running (no downstream checks)
/health/ready  -> readiness: are MySQL and Redis actually reachable
/version       -> build metadata, useful for confirming what's deployed
"""
from fastapi import APIRouter

from app.core.config import settings
from app.core.database import check_db_connection
from app.core.logging import get_logger
from app.core.redis_client import check_redis_connection
from app.schemas.health import HealthResponse, ReadinessResponse, VersionResponse

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app_name=settings.APP_NAME, version=settings.APP_VERSION)


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    overall = "ready" if (db_ok and redis_ok) else "degraded"
    if overall != "ready":
        logger.warning("Readiness check degraded: db_ok=%s redis_ok=%s", db_ok, redis_ok)

    return ReadinessResponse(
        status=overall,
        database="up" if db_ok else "down",
        redis="up" if redis_ok else "down",
    )


@router.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    return VersionResponse(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )
