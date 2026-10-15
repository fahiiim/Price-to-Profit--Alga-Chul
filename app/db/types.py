"""Custom column types that keep money exact and timestamps timezone-aware."""

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Dialect, Enum, Integer
from sqlalchemy.types import TypeDecorator


class ScaledDecimal(TypeDecorator[Decimal]):
    """Store an exact `Decimal` as an integer count of its smallest unit.

    With `scale=2`, `Decimal("2104.50")` is stored as `210450`. SQLite has no
    exact decimal type, so this avoids float rounding and lets SQL `SUM` stay
    exact. The same column works unchanged on PostgreSQL.
    """

    impl = Integer
    cache_ok = True

    def __init__(self, scale: int = 2) -> None:
        super().__init__()
        self.scale = scale
        self._factor = Decimal(10) ** scale
        self._quantum = Decimal(1).scaleb(-scale)

    def process_bind_param(
        self, value: Decimal | int | None, dialect: Dialect
    ) -> int | None:
        if value is None:
            return None
        scaled = Decimal(value) * self._factor
        return int(scaled.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    def process_result_value(
        self, value: int | None, dialect: Dialect
    ) -> Decimal | None:
        if value is None:
            return None
        return (Decimal(value) / self._factor).quantize(self._quantum)


class UTCDateTime(TypeDecorator[datetime]):
    """Store datetimes as naive UTC and always return them as aware UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetimes are not allowed; use UTC.")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


def str_enum(enum_class: type[StrEnum]) -> Enum:
    """Store a `StrEnum` as its plain string value in a VARCHAR column."""
    return Enum(
        enum_class,
        native_enum=False,
        length=32,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
