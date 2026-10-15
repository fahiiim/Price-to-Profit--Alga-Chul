"""Read and change the single platform settings row."""

from sqlalchemy.orm import Session

from app.activity.enums import ActivityAction
from app.activity.service import record_activity
from app.core.errors import NotFoundError
from app.platform.models import PlatformSettings, QuoteDefaultsMixin
from app.platform.schemas import AppSettingsUpdate, QuoteDefaults

PLATFORM_SETTINGS_ID = 1
ENTITY_TYPE = "platform"


def ensure_platform_settings(session: Session) -> PlatformSettings:
    """Return the settings row, creating it with defaults on first start."""
    settings = session.get(PlatformSettings, PLATFORM_SETTINGS_ID)
    if settings is None:
        settings = PlatformSettings(id=PLATFORM_SETTINGS_ID)
        session.add(settings)
        session.flush()
    return settings


def get_platform_settings(session: Session) -> PlatformSettings:
    settings = session.get(PlatformSettings, PLATFORM_SETTINGS_ID)
    if settings is None:
        raise NotFoundError("Platform settings have not been initialised.")
    return settings


def copy_quote_defaults(
    source: QuoteDefaultsMixin | QuoteDefaults, target: QuoteDefaultsMixin
) -> None:
    """Copy every quote default field from `source` onto `target`."""
    for name in QuoteDefaults.model_fields:
        setattr(target, name, getattr(source, name))


def replace_quote_defaults(
    session: Session, settings: PlatformSettings, payload: QuoteDefaults
) -> PlatformSettings:
    copy_quote_defaults(payload, settings)
    record_activity(
        session,
        action=ActivityAction.DEFAULTS_UPDATED,
        entity_type=ENTITY_TYPE,
        entity_id=settings.id,
        summary="Quote defaults updated",
    )
    session.commit()
    return settings


def update_app_settings(
    session: Session, settings: PlatformSettings, payload: AppSettingsUpdate
) -> PlatformSettings:
    changes = payload.model_dump(exclude_unset=True)
    for name, value in changes.items():
        setattr(settings, name, value)
    record_activity(
        session,
        action=ActivityAction.APP_SETTINGS_UPDATED,
        entity_type=ENTITY_TYPE,
        entity_id=settings.id,
        summary=f"App settings updated: {', '.join(sorted(changes)) or 'no changes'}",
    )
    session.commit()
    return settings
