from decimal import Decimal

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import ScaledDecimal, str_enum
from app.pricing.enums import DepositMode

DEFAULT_QUOTE_TERMS = (
    "This quote is valid until the date shown. A deposit secures your "
    "appointment and is non-refundable within 48 hours of the booking."
)
DEFAULT_INVOICE_TERMS = (
    "Payment is due by the date shown. Please use the payment link or "
    "contact us for bank transfer details."
)


class QuoteDefaultsMixin:
    """Pricing defaults. Shared by `PlatformSettings` and `BusinessProfile`.

    The admin edits the platform copy. It seeds new business profiles and can
    be re-applied to an existing profile on request.
    """

    currency: Mapped[str] = mapped_column(String(3), default="AED")
    tax_label: Mapped[str] = mapped_column(String(20), default="VAT")
    tax_rate_percent: Mapped[Decimal] = mapped_column(
        ScaledDecimal(), default=Decimal("5")
    )
    hourly_rate: Mapped[Decimal] = mapped_column(
        ScaledDecimal(), default=Decimal("180")
    )
    default_markup_percent: Mapped[Decimal] = mapped_column(
        ScaledDecimal(), default=Decimal("60")
    )
    deposit_mode: Mapped[DepositMode] = mapped_column(
        str_enum(DepositMode), default=DepositMode.PERCENT
    )
    deposit_value: Mapped[Decimal] = mapped_column(
        ScaledDecimal(), default=Decimal("30")
    )
    whole_packs_default: Mapped[bool] = mapped_column(Boolean, default=True)
    quote_validity_days: Mapped[int] = mapped_column(Integer, default=14)
    invoice_due_days: Mapped[int] = mapped_column(Integer, default=7)
    quote_terms: Mapped[str] = mapped_column(Text, default=DEFAULT_QUOTE_TERMS)
    invoice_terms: Mapped[str] = mapped_column(Text, default=DEFAULT_INVOICE_TERMS)


class PlatformSettings(QuoteDefaultsMixin, TimestampMixin, Base):
    """Single-row table (id = 1) with admin-controlled settings."""

    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    support_email: Mapped[str | None] = mapped_column(String(254))
    support_whatsapp: Mapped[str | None] = mapped_column(String(40))
    terms_url: Mapped[str | None] = mapped_column(String(500))
    privacy_url: Mapped[str | None] = mapped_column(String(500))
    minimum_app_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    latest_app_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_message: Mapped[str | None] = mapped_column(String(500))
