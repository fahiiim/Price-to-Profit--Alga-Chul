from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utc_now
from app.db.base import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.business.models import BusinessProfile


class User(TimestampMixin, Base):
    """A stylist's account. Verified by OTP, signed in with email and password."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    email_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    otp_hash: Mapped[str | None] = mapped_column(String(64))
    otp_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    otp_attempts: Mapped[int] = mapped_column(Integer, default=0)

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    businesses: Mapped[list["BusinessProfile"]] = relationship(back_populates="owner")

    @property
    def is_verified(self) -> bool:
        return self.email_verified_at is not None


class AuthSession(Base):
    """A signed-in device. `token_hash` is SHA-256 of the bearer token."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)

    user: Mapped[User] = relationship(back_populates="sessions", lazy="joined")
