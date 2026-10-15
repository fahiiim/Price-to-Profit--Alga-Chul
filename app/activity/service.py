"""Write and read activity log entries.

`record_activity` only adds the entry to the session. The calling service
commits it together with the change it describes, so the log never records
something that was rolled back.
"""

from sqlalchemy import func, select
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
) -> None:
    session.add(
        ActivityLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary[:300],
        )
    )


def list_activity(
    session: Session,
    *,
    entity_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[ActivityLog], int]:
    """Return newest-first entries and the total matching count."""
    statement = select(ActivityLog)
    if entity_type:
        statement = statement.where(ActivityLog.entity_type == entity_type)

    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    items = session.scalars(
        statement.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(items), total or 0
