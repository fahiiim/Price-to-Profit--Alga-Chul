from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import ScaledDecimal, UTCDateTime, str_enum
from app.pricing.enums import DepositMode, LineKind
from app.quotes.policy import QuoteStatus

if TYPE_CHECKING:
    from app.invoices.models import Invoice


class Quote(TimestampMixin, Base):
    """A priced proposal for one client.

    Currency, tax rate and every calculated total are stored on the quote, so
    later changes to the business defaults never change an existing quote.
    """

    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[str] = mapped_column(String(20), unique=True)
    status: Mapped[QuoteStatus] = mapped_column(
        str_enum(QuoteStatus), default=QuoteStatus.DRAFT, index=True
    )
    title: Mapped[str | None] = mapped_column(String(120))

    client_name: Mapped[str] = mapped_column(String(120), index=True)
    client_phone: Mapped[str | None] = mapped_column(String(40))
    client_email: Mapped[str | None] = mapped_column(String(254))

    appointment_date: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    currency: Mapped[str] = mapped_column(String(3))
    tax_label: Mapped[str] = mapped_column(String(20))
    tax_rate_percent: Mapped[Decimal] = mapped_column(ScaledDecimal())
    deposit_mode: Mapped[DepositMode] = mapped_column(str_enum(DepositMode))
    deposit_value: Mapped[Decimal] = mapped_column(ScaledDecimal())

    subtotal: Mapped[Decimal] = mapped_column(ScaledDecimal())
    taxable_amount: Mapped[Decimal] = mapped_column(ScaledDecimal())
    tax_amount: Mapped[Decimal] = mapped_column(ScaledDecimal())
    total: Mapped[Decimal] = mapped_column(ScaledDecimal())
    deposit_amount: Mapped[Decimal] = mapped_column(ScaledDecimal())
    balance_due: Mapped[Decimal] = mapped_column(ScaledDecimal())
    total_cost: Mapped[Decimal] = mapped_column(ScaledDecimal())
    profit: Mapped[Decimal] = mapped_column(ScaledDecimal())
    labour_hours: Mapped[Decimal] = mapped_column(ScaledDecimal())
    profit_per_hour: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    margin_percent: Mapped[Decimal | None] = mapped_column(ScaledDecimal())

    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    lines: Mapped[list["QuoteLine"]] = relationship(
        back_populates="quote",
        cascade="all, delete-orphan",
        order_by="QuoteLine.position",
        lazy="selectin",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        back_populates="quote", lazy="selectin"
    )


class QuoteLine(Base):
    """One line of a quote: its inputs and the calculated price and cost.

    Only the input columns that match `kind` are filled in.
    """

    __tablename__ = "quote_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), index=True
    )
    library_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("library_items.id", ondelete="SET NULL")
    )
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[LineKind] = mapped_column(str_enum(LineKind))
    description: Mapped[str] = mapped_column(String(200))
    taxable: Mapped[bool] = mapped_column(Boolean)

    grams_required: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    grams_per_pack: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    pack_price: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    markup_percent: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    whole_packs: Mapped[bool | None] = mapped_column(Boolean)
    hours: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    hourly_rate: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    quantity: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    unit_price: Mapped[Decimal | None] = mapped_column(ScaledDecimal())
    unit_cost: Mapped[Decimal | None] = mapped_column(ScaledDecimal())

    price: Mapped[Decimal] = mapped_column(ScaledDecimal())
    cost: Mapped[Decimal] = mapped_column(ScaledDecimal())
    cost_per_gram: Mapped[Decimal | None] = mapped_column(ScaledDecimal(scale=4))
    packs_needed: Mapped[int | None] = mapped_column(Integer)
    leftover_grams: Mapped[Decimal | None] = mapped_column(ScaledDecimal())

    quote: Mapped[Quote] = relationship(back_populates="lines")
