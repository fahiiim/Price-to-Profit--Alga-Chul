"""Create the rows the application needs before it can serve requests."""

from sqlalchemy.orm import Session

from app.platform.service import ensure_platform_settings


def seed_required_rows(session: Session) -> None:
    """Ensure the platform settings row exists.

    Businesses are created through `POST /v1/businesses` (first-launch setup),
    not seeded. Safe to run on every start: an existing row is left untouched.
    """
    ensure_platform_settings(session)
    session.commit()
