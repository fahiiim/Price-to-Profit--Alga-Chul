from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.schemas import Grams, Hours, MarkupPercent, Money, Percent, Quantity
from app.pricing.enums import DepositMode, LineKind
from app.quotes.models import Quote
from app.quotes.policy import QuoteStatus

WORKED_EXAMPLE = {
    "client": {
        "name": "Sara Ahmed",
        "phone": "+971501112233",
        "email": "sara@example.com",
    },
    "title": "Full head tape-ins",
    "appointment_date": "2026-11-02",
    "lines": [
        {
            "kind": "hair",
            "description": "Russian tape-ins 20in, #60",
            "grams_required": "170",
            "grams_per_pack": "100",
            "pack_price": "350.00",
            "markup_percent": "60",
            "whole_packs": True,
        },
        {
            "kind": "labour",
            "description": "Installation",
            "hours": "3.5",
            "hourly_rate": "180.00",
        },
        {
            "kind": "material",
            "description": "Tape tabs and remover",
            "unit_price": "80.00",
            "unit_cost": "40.00",
        },
        {"kind": "service", "description": "Toning", "unit_price": "150.00"},
        {
            "kind": "fee",
            "description": "Shipping",
            "unit_price": "25.00",
            "unit_cost": "25.00",
            "taxable": False,
        },
    ],
    "deposit": {"mode": "fixed", "value": "600.00"},
    "tax_rate_percent": "5",
    "notes": "Includes a free 2-week check-up.",
}
"""The worked example from the product spec. Totals: subtotal 2,005.00,
VAT 99.00, total 2,104.00, balance 1,504.00, profit 1,240.00, 354.29/hour."""


class ClientDetails(BaseModel):
    """The stylist's client. Printed on the quote and invoice."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=120, examples=["Sara Ahmed"])
    phone: str | None = Field(default=None, max_length=40, examples=["+971501112233"])
    email: EmailStr | None = Field(default=None, examples=["sara@example.com"])


class DepositInput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mode: DepositMode = Field(
        description="`percent` of the total, or a `fixed` amount."
    )
    value: Money = Field(
        description="Percentage (0-100) or amount, depending on `mode`.",
        examples=["30.00"],
    )

    @model_validator(mode="after")
    def _check_percent(self) -> Self:
        if self.mode is DepositMode.PERCENT and self.value > 100:
            raise ValueError("A percentage deposit cannot be more than 100.")
        return self


class QuoteLineInput(BaseModel):
    """One line of a quote, as sent by the app.

    Values are resolved in this order: the value on the line, then the
    library item (`library_item_id`), then the business defaults.

    | kind | required | defaults |
    | --- | --- | --- |
    | `hair` | `grams_required`, `grams_per_pack`, `pack_price` | `markup_percent`, `whole_packs` from the business |
    | `labour` | `hours` | `hourly_rate` from the business |
    | `service`, `material`, `fee` | `unit_price` | `quantity` = 1, `unit_cost` = 0 |
    """  # noqa: E501

    kind: LineKind | None = Field(
        default=None,
        description="Line type. Optional when `library_item_id` is given.",
    )
    library_item_id: int | None = Field(
        default=None, description="Pre-fill this line from a library item."
    )
    description: str | None = Field(
        default=None,
        max_length=200,
        description="Text printed on the quote. Defaults to the item name.",
    )
    taxable: bool | None = Field(
        default=None,
        description="Whether VAT applies. Defaults to the item's setting or true.",
    )

    grams_required: Grams | None = Field(
        default=None, description="Hair: grams the client needs.", examples=["170"]
    )
    grams_per_pack: Grams | None = Field(
        default=None, description="Hair: grams in one pack.", examples=["100"]
    )
    pack_price: Money | None = Field(
        default=None, description="Hair: cost of one pack.", examples=["350.00"]
    )
    markup_percent: MarkupPercent | None = Field(
        default=None, description="Hair: markup on the hair cost.", examples=["60"]
    )
    whole_packs: bool | None = Field(
        default=None,
        description="Hair: charge whole packs (true) or only the grams used.",
    )
    hours: Hours | None = Field(
        default=None, description="Labour: hours of work.", examples=["3.5"]
    )
    hourly_rate: Money | None = Field(
        default=None, description="Labour: price per hour.", examples=["180.00"]
    )
    quantity: Quantity | None = Field(
        default=None, description="Service/material/fee: number of units."
    )
    unit_price: Money | None = Field(
        default=None, description="Service/material/fee: price per unit."
    )
    unit_cost: Money | None = Field(
        default=None, description="Service/material/fee: your cost per unit."
    )


class QuoteCreate(BaseModel):
    """A new quote. It is priced immediately and saved as a `draft`."""

    model_config = ConfigDict(json_schema_extra={"examples": [WORKED_EXAMPLE]})

    client: ClientDetails
    title: str | None = Field(
        default=None, max_length=120, examples=["Full head tape-ins"]
    )
    appointment_date: date | None = None
    valid_until: date | None = Field(
        default=None,
        description="Defaults to today + the business `quote_validity_days`.",
    )
    lines: list[QuoteLineInput] = Field(min_length=1, max_length=100)
    deposit: DepositInput | None = Field(
        default=None, description="Defaults to the business deposit setting."
    )
    tax_rate_percent: Percent | None = Field(
        default=None, description="Defaults to the business tax rate."
    )
    notes: str | None = Field(
        default=None, max_length=2000, description="Printed on the client quote."
    )
    internal_notes: str | None = Field(
        default=None, max_length=2000, description="Never printed for the client."
    )


class QuoteUpdate(BaseModel):
    """Partial update. Only the fields you send are changed.

    Sending `lines` replaces every line. Changing `lines`, `deposit` or
    `tax_rate_percent` re-prices the quote. Invoiced quotes cannot be edited.
    """

    client: ClientDetails | None = None
    title: str | None = Field(default=None, max_length=120)
    appointment_date: date | None = None
    valid_until: date | None = None
    lines: list[QuoteLineInput] | None = Field(
        default=None, min_length=1, max_length=100
    )
    deposit: DepositInput | None = None
    tax_rate_percent: Percent | None = None
    notes: str | None = Field(default=None, max_length=2000)
    internal_notes: str | None = Field(default=None, max_length=2000)


class QuotePreviewRequest(BaseModel):
    """Lines to price without saving anything."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "lines": WORKED_EXAMPLE["lines"],
                    "deposit": WORKED_EXAMPLE["deposit"],
                    "tax_rate_percent": "5",
                }
            ]
        }
    )

    lines: list[QuoteLineInput] = Field(min_length=1, max_length=100)
    deposit: DepositInput | None = None
    tax_rate_percent: Percent | None = None


class QuoteStatusUpdate(BaseModel):
    """Move a quote through its lifecycle.

    Allowed: draft -> sent/accepted/declined, sent -> draft/accepted/declined,
    accepted -> sent/declined, declined -> draft/sent. A quote becomes
    `invoiced` only by creating its invoice.
    """

    status: QuoteStatus


class PricedLineRead(BaseModel):
    """A line with its resolved inputs and calculated results."""

    model_config = ConfigDict(from_attributes=True)

    kind: LineKind
    description: str
    library_item_id: int | None
    taxable: bool

    grams_required: Decimal | None = None
    grams_per_pack: Decimal | None = None
    pack_price: Decimal | None = None
    markup_percent: Decimal | None = None
    whole_packs: bool | None = None
    hours: Decimal | None = None
    hourly_rate: Decimal | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    unit_cost: Decimal | None = None

    price: Decimal = Field(description="Amount charged to the client, before VAT.")
    cost: Decimal = Field(description="What this line costs the stylist.")
    cost_per_gram: Decimal | None = Field(
        default=None, description="Hair: pack price / grams per pack."
    )
    packs_needed: int | None = Field(
        default=None, description="Hair: packs to buy (rounded up)."
    )
    leftover_grams: Decimal | None = Field(
        default=None, description="Hair: grams left over from whole packs."
    )


class QuoteLineRead(PricedLineRead):
    id: int
    position: int = Field(description="1-based order of the line on the quote.")


class QuoteTotalsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subtotal: Decimal = Field(description="Sum of line prices.")
    taxable_amount: Decimal = Field(description="Sum of taxable line prices.")
    tax_amount: Decimal = Field(description="taxable_amount x tax rate.")
    total: Decimal = Field(description="subtotal + tax_amount.")
    deposit_amount: Decimal = Field(description="Deposit requested up front.")
    balance_due: Decimal = Field(description="total - deposit_amount.")
    total_cost: Decimal = Field(description="Sum of line costs.")
    profit: Decimal = Field(description="total - tax_amount - total_cost.")
    labour_hours: Decimal = Field(description="Sum of labour line hours.")
    profit_per_hour: Decimal | None = Field(
        description="profit / labour_hours. Null without labour."
    )
    margin_percent: Decimal | None = Field(
        description="profit / subtotal x 100. Null when the subtotal is 0."
    )


class QuotePricingRead(BaseModel):
    currency: str
    tax_label: str
    tax_rate_percent: Decimal
    deposit: DepositInput


class QuotePreviewRead(QuotePricingRead):
    """The result of pricing lines without saving them."""

    lines: list[PricedLineRead]
    totals: QuoteTotalsRead


class QuoteRead(QuotePricingRead):
    id: int
    number: str = Field(examples=["Q-0001"])
    status: QuoteStatus
    title: str | None
    client: ClientDetails
    appointment_date: date | None
    valid_until: date | None
    notes: str | None
    internal_notes: str | None
    lines: list[QuoteLineRead]
    totals: QuoteTotalsRead
    invoice_id: int | None = Field(description="Set once the quote is invoiced.")
    sent_at: datetime | None
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, quote: Quote) -> Self:
        return cls(
            id=quote.id,
            number=quote.number,
            status=quote.status,
            title=quote.title,
            client=ClientDetails(
                name=quote.client_name,
                phone=quote.client_phone,
                email=quote.client_email,
            ),
            appointment_date=quote.appointment_date,
            valid_until=quote.valid_until,
            notes=quote.notes,
            internal_notes=quote.internal_notes,
            currency=quote.currency,
            tax_label=quote.tax_label,
            tax_rate_percent=quote.tax_rate_percent,
            deposit=DepositInput(mode=quote.deposit_mode, value=quote.deposit_value),
            lines=[QuoteLineRead.model_validate(line) for line in quote.lines],
            totals=QuoteTotalsRead.model_validate(quote),
            invoice_id=quote.invoice.id if quote.invoice else None,
            sent_at=quote.sent_at,
            accepted_at=quote.accepted_at,
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )


class QuoteSummary(BaseModel):
    """A compact quote for lists and the home screen."""

    id: int
    number: str
    status: QuoteStatus
    title: str | None
    client_name: str
    appointment_date: date | None
    currency: str
    total: Decimal
    profit: Decimal
    invoice_id: int | None
    created_at: datetime

    @classmethod
    def from_model(cls, quote: Quote) -> Self:
        return cls(
            id=quote.id,
            number=quote.number,
            status=quote.status,
            title=quote.title,
            client_name=quote.client_name,
            appointment_date=quote.appointment_date,
            currency=quote.currency,
            total=quote.total,
            profit=quote.profit,
            invoice_id=quote.invoice.id if quote.invoice else None,
            created_at=quote.created_at,
        )
