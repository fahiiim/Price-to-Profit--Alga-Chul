"""Write and read activity log entries.

`record_activity` only adds the entry to the session. The calling service
commits it together with the change it describes, so the log never records
something that was rolled back.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.activity.enums import ActivityAction
from app.activity.models import ActivityLog


def record_activity(
    session: Session,
    *,
    action: ActivityAction,
    entity_type: str,
    entity_id: int | None,
    summary: str,
    business_id: int | None = None,
) -> None:
    session.add(
        ActivityLog(
            business_id=business_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary[:300],
        )
    )


def list_activity(
    session: Session,
    *,
    business_id: int | None = None,
    entity_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[ActivityLog], int]:
    """Return newest-first entries and the total matching count."""
    statement = select(ActivityLog)
    if business_id is not None:
        statement = statement.where(
            or_(
                ActivityLog.business_id == business_id,
                ActivityLog.business_id.is_(None),
            )
        )
    if entity_type:
        statement = statement.where(ActivityLog.entity_type == entity_type)

    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    items = session.scalars(
        statement.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(items), total or 0
