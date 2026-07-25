"""Pydantic response models for health/readiness/version endpoints."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    redis: str


class VersionResponse(BaseModel):
    app_name: str
    version: str
    environment: str
