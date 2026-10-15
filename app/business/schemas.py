from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.core.schemas import HttpLink, MarkupPercent, Money, Percent
from app.platform.schemas import QuoteDefaults
from app.pricing.enums import DepositMode

PREFIX_PATTERN = r"^[A-Z0-9]{1,10}$"
LOGO_URL = "/v1/business/logo"


class BusinessRead(QuoteDefaults):
    """The full business profile, including its pricing defaults."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    business_name: str = Field(examples=["Amna Hair Studio"])
    owner_name: str | None = Field(examples=["Amna"])
    phone: str | None = Field(examples=["+971501234567"])
    email: str | None = Field(examples=["hello@amnahair.ae"])
    address: str | None = Field(examples=["Jumeirah Lake Towers, Dubai"])
    instagram: str | None = Field(examples=["@amnahair"])
    website: str | None = Field(examples=["https://amnahair.ae"])
    tax_registration_number: str | None = Field(
        description="VAT registration number (TRN) printed on invoices.",
        examples=["100123456700003"],
    )
    payment_link: str | None = Field(
        description="Link printed on quotes and invoices so clients can pay.",
        examples=["https://pay.example.com/amnahair"],
    )
    quote_prefix: str = Field(examples=["Q"])
    invoice_prefix: str = Field(examples=["INV"])
    next_quote_number: int = Field(description="Number the next quote will use.")
    next_invoice_number: int = Field(description="Number the next invoice will use.")
    logo_path: str | None = Field(default=None, exclude=True)
    created_at: datetime
    updated_at: datetime

    @computed_field(description="Where to download the logo, or null if none.")
    @property
    def logo_url(self) -> str | None:
        return LOGO_URL if self.logo_path else None


class BusinessUpdate(BaseModel):
    """Partial update. Only the fields you send are changed.

    Send `null` to clear an optional text field such as `instagram`.
    """

    business_name: str | None = Field(default=None, min_length=1, max_length=120)
    owner_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=300)
    instagram: str | None = Field(default=None, max_length=60)
    website: HttpLink | None = None
    tax_registration_number: str | None = Field(default=None, max_length=40)
    payment_link: HttpLink | None = None
    quote_prefix: str | None = Field(default=None, pattern=PREFIX_PATTERN)
    invoice_prefix: str | None = Field(default=None, pattern=PREFIX_PATTERN)

    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    tax_label: str | None = Field(default=None, min_length=1, max_length=20)
    tax_rate_percent: Percent | None = None
    hourly_rate: Money | None = None
    default_markup_percent: MarkupPercent | None = None
    deposit_mode: DepositMode | None = None
    deposit_value: Money | None = None
    whole_packs_default: bool | None = None
    quote_validity_days: int | None = Field(default=None, ge=1, le=365)
    invoice_due_days: int | None = Field(default=None, ge=0, le=365)
    quote_terms: str | None = Field(default=None, max_length=2000)
    invoice_terms: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "business_name": "Amna Hair Studio",
                    "phone": "+971501234567",
                    "payment_link": "https://pay.example.com/amnahair",
                    "hourly_rate": "180.00",
                    "default_markup_percent": "60.00",
                }
            ]
        }
    )


REQUIRED_FIELDS = frozenset(
    {
        "business_name",
        "quote_prefix",
        "invoice_prefix",
        "currency",
        "tax_label",
        "tax_rate_percent",
        "hourly_rate",
        "default_markup_percent",
        "deposit_mode",
        "deposit_value",
        "whole_packs_default",
        "quote_validity_days",
        "invoice_due_days",
        "quote_terms",
        "invoice_terms",
    }
)
"""Fields that cannot be cleared with `null`."""
