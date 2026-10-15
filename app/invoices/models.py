from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import ScaledDecimal, UTCDateTime, str_enum
from app.invoices.policy import InvoiceStatus
from app.quotes.models import Quote


class Invoice(TimestampMixin, Base):
    """A bill created from exactly one quote.

    Money totals, the payment link and the terms are copied from the quote and
    business at creation time, so the invoice never changes afterwards.
    """

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True
    )
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="RESTRICT"), unique=True
    )
    number: Mapped[str] = mapped_column(String(20), unique=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        str_enum(InvoiceStatus), default=InvoiceStatus.UNPAID, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, index=True)
    due_date: Mapped[date] = mapped_column(Date)
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    currency: Mapped[str] = mapped_column(String(3))
    subtotal: Mapped[Decimal] = mapped_column(ScaledDecimal())
    tax_amount: Mapped[Decimal] = mapped_column(ScaledDecimal())
    total: Mapped[Decimal] = mapped_column(ScaledDecimal())
    deposit_amount: Mapped[Decimal] = mapped_column(ScaledDecimal())
    amount_paid: Mapped[Decimal] = mapped_column(ScaledDecimal())

    payment_link: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)

    quote: Mapped[Quote] = relationship(back_populates="invoice", lazy="selectin")
