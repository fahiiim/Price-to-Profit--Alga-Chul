"""Create the rows the application needs before it can serve requests."""

from sqlalchemy.orm import Session

from app.business.service import ensure_business
from app.platform.service import ensure_platform_settings


def seed_required_rows(session: Session) -> None:
    """Ensure the platform settings row and the business profile exist.

    Safe to run on every start: existing rows are left untouched.
    """
    settings = ensure_platform_settings(session)
    ensure_business(session, settings)
    session.commit()
