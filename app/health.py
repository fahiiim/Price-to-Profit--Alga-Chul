from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.dependencies import SessionDep, SettingsDep

router = APIRouter(prefix="/health", tags=["Health"])


class LiveStatus(BaseModel):
    status: str = Field(examples=["ok"])
    version: str = Field(examples=["0.1.0"])
    environment: str = Field(examples=["local"])


class ReadyStatus(BaseModel):
    status: str = Field(examples=["ready"])
    database: str = Field(examples=["ok"])


@router.get(
    "/live",
    response_model=LiveStatus,
    summary="Liveness probe",
    description="Returns 200 while the process is running. Touches nothing else.",
)
def live(settings: SettingsDep) -> LiveStatus:
    return LiveStatus(
        status="ok", version=settings.app_version, environment=settings.environment
    )


@router.get(
    "/ready",
    response_model=ReadyStatus,
    summary="Readiness probe",
    description="Returns 200 when the database answers a simple query.",
)
def ready(session: SessionDep) -> ReadyStatus:
    session.execute(text("SELECT 1"))
    return ReadyStatus(status="ready", database="ok")
