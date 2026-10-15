from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.activity.enums import ActivityAction
from app.core.clock import utc_now
from app.db.base import Base
from app.db.types import UTCDateTime, str_enum


class ActivityLog(Base):
    """One recorded change, e.g. "Quote Q-0007 created for Sara"."""

    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[ActivityAction] = mapped_column(str_enum(ActivityAction))
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utc_now, index=True
    )
