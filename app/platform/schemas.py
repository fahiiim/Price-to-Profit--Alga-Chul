from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.schemas import HttpLink, MarkupPercent, Money, Percent
from app.pricing.enums import DepositMode

VERSION_PATTERN = r"^\d+\.\d+\.\d+$"


class QuoteDefaults(BaseModel):
    """Pricing defaults used when a new quote does not override them."""

    model_config = ConfigDict(from_attributes=True)

    currency: str = Field(
        pattern=r"^[A-Z]{3}$",
        description="ISO 4217 currency code shown on every document.",
        examples=["AED"],
    )
    tax_label: str = Field(
        min_length=1,
        max_length=20,
        description="Name of the sales tax on documents.",
        examples=["VAT"],
    )
    tax_rate_percent: Percent = Field(
        description="Tax rate applied to taxable lines.", examples=["5.00"]
    )
    hourly_rate: Money = Field(
        description="Default price per hour for labour lines.", examples=["180.00"]
    )
    default_markup_percent: MarkupPercent = Field(
        description="Markup added to the cost of hair lines.", examples=["60.00"]
    )
    deposit_mode: DepositMode = Field(
        description="Whether `deposit_value` is a percentage or a fixed amount."
    )
    deposit_value: Money = Field(
        description="Deposit as a percentage (0-100) or a fixed amount.",
        examples=["30.00"],
    )
    whole_packs_default: bool = Field(
        description="Charge hair in whole packs (true) or by the gram (false)."
    )
    quote_validity_days: int = Field(
        ge=1, le=365, description="Days a new quote stays valid.", examples=[14]
    )
    invoice_due_days: int = Field(
        ge=0, le=365, description="Days until a new invoice is due.", examples=[7]
    )
    quote_terms: str = Field(max_length=2000, description="Terms printed on quotes.")
    invoice_terms: str = Field(
        max_length=2000, description="Terms printed on invoices."
    )

    @model_validator(mode="after")
    def _check_deposit(self) -> Self:
        if self.deposit_mode is DepositMode.PERCENT and self.deposit_value > 100:
            raise ValueError("A percentage deposit cannot be more than 100.")
        return self


class QuoteDefaultsRead(QuoteDefaults):
    updated_at: datetime


class AppSettings(BaseModel):
    """Configuration the mobile app reads on launch."""

    model_config = ConfigDict(from_attributes=True)

    support_email: EmailStr | None = Field(
        description="Where stylists can get help.", examples=["help@pricetoprofit.app"]
    )
    support_whatsapp: str | None = Field(
        max_length=40,
        description="WhatsApp number for support, in international format.",
        examples=["+971500000000"],
    )
    terms_url: HttpLink | None = Field(description="Terms of service page.")
    privacy_url: HttpLink | None = Field(description="Privacy policy page.")
    minimum_app_version: str = Field(
        pattern=VERSION_PATTERN,
        description="Older app versions must update before continuing.",
        examples=["1.0.0"],
    )
    latest_app_version: str = Field(
        pattern=VERSION_PATTERN,
        description="Newest version in the stores. Older apps may show a hint.",
        examples=["1.2.0"],
    )
    maintenance_mode: bool = Field(
        description="When true the app shows `maintenance_message` and pauses."
    )
    maintenance_message: str | None = Field(
        max_length=500, description="Message shown during maintenance."
    )


class AppSettingsRead(AppSettings):
    updated_at: datetime


class AppSettingsUpdate(BaseModel):
    """Partial update. Only the fields you send are changed."""

    support_email: EmailStr | None = None
    support_whatsapp: str | None = Field(default=None, max_length=40)
    terms_url: HttpLink | None = None
    privacy_url: HttpLink | None = None
    minimum_app_version: str | None = Field(default=None, pattern=VERSION_PATTERN)
    latest_app_version: str | None = Field(default=None, pattern=VERSION_PATTERN)
    maintenance_mode: bool | None = None
    maintenance_message: str | None = Field(default=None, max_length=500)
