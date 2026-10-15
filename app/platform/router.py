from fastapi import APIRouter

from app.core.dependencies import SessionDep
from app.platform.models import PlatformSettings
from app.platform.schemas import AppSettings
from app.platform.service import get_platform_settings

router = APIRouter(prefix="/app-config", tags=["App config"])


@router.get(
    "",
    response_model=AppSettings,
    summary="Get mobile app configuration",
    description=(
        "Read on every app launch. Tells the app whether it must update "
        "(`minimum_app_version`), whether maintenance mode is on, and where "
        "to send users for support, terms and privacy."
    ),
    response_description="Current public app configuration.",
)
def get_app_config(session: SessionDep) -> PlatformSettings:
    return get_platform_settings(session)
