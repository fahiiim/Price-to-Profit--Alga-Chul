from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.platform.models import QuoteDefaultsMixin


class BusinessProfile(QuoteDefaultsMixin, TimestampMixin, Base):
    """The stylist's business. Printed on every quote, invoice and cost sheet.

    Many businesses can exist. Each request names one with the
    `X-Business-Id` header until login is added.
    """

    __tablename__ = "business_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_name: Mapped[str] = mapped_column(String(120))
    owner_name: Mapped[str | None] = mapped_column(String(120))
    tagline: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(254))
    address: Mapped[str | None] = mapped_column(String(300))
    instagram: Mapped[str | None] = mapped_column(String(60))
    website: Mapped[str | None] = mapped_column(String(500))
    tax_registration_number: Mapped[str | None] = mapped_column(String(40))
    payment_link: Mapped[str | None] = mapped_column(String(500))
    logo_path: Mapped[str | None] = mapped_column(String(255))

    quote_prefix: Mapped[str] = mapped_column(String(10), default="Q")
    invoice_prefix: Mapped[str] = mapped_column(String(10), default="INV")
    next_quote_number: Mapped[int] = mapped_column(Integer, default=1)
    next_invoice_number: Mapped[int] = mapped_column(Integer, default=1)
