"""Single source of the current time, so every timestamp is timezone-aware UTC."""

from datetime import UTC, date, datetime


def utc_now() -> datetime:
    """Return the current moment as an aware UTC datetime."""
    return datetime.now(UTC)


def today() -> date:
    """Return today's date in UTC."""
    return utc_now().date()
