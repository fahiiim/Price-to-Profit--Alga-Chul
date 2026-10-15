from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import ScaledDecimal, str_enum
from app.pricing.enums import LineKind


class LibraryItem(TimestampMixin, Base):
    """A reusable product or service that pre-fills quote lines.

    Only the pricing columns that match `kind` are used; see
    `app.library.rules.KIND_FIELDS`.
    """

    __tablename__ = "library_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[LineKind] = mapped_column(str_enum(LineKind), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(60))
    taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    grams_per_pack: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    pack_price: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    markup_percent: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    hourly_rate: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    unit_price: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    unit_cost: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    unit_label: Mapped[str | None] = mapped_column(String(20))
