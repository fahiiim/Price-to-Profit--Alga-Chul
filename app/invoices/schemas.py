from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field

from app.invoices.models import Invoice
from app.invoices.policy import InvoiceStatus
from app.quotes.schemas import ClientDetails, QuoteLineRead


class InvoiceCreate(BaseModel):
    """Optional details for a new invoice. An empty body `{}` is fine."""

    issue_date: date | None = Field(default=None, description="Defaults to today.")
    due_date: date | None = Field(
        default=None,
        description="Defaults to issue date + the business `invoice_due_days`.",
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Printed on the invoice. Defaults to the quote notes.",
    )


class InvoiceStatusUpdate(BaseModel):
    """Record a payment. Any status can be set, including undoing a payment.

    `amount_paid` follows the status: 0 for `unpaid`, the deposit for
    `deposit_paid` and the total for `paid`.
    """

    status: InvoiceStatus


class InvoiceSummary(BaseModel):
    id: int
    number: str = Field(examples=["INV-0001"])
    status: InvoiceStatus
    quote_id: int
    quote_number: str
    client_name: str
    issue_date: date
    due_date: date
    currency: str
    total: Decimal
    amount_due: Decimal = Field(description="total - amount_paid.")
    created_at: datetime

    @classmethod
    def from_model(cls, invoice: Invoice) -> Self:
        return cls(
            id=invoice.id,
            number=invoice.number,
            status=invoice.status,
            quote_id=invoice.quote_id,
            quote_number=invoice.quote.number,
            client_name=invoice.quote.client_name,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            currency=invoice.currency,
            total=invoice.total,
            amount_due=invoice.total - invoice.amount_paid,
            created_at=invoice.created_at,
        )


class InvoiceRead(InvoiceSummary):
    client: ClientDetails
    paid_at: datetime | None
    tax_label: str
    tax_rate_percent: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    deposit_amount: Decimal = Field(description="Deposit requested on the quote.")
    amount_paid: Decimal = Field(description="Received so far, based on status.")
    payment_link: str | None
    notes: str | None
    terms: str | None
    lines: list[QuoteLineRead]
    updated_at: datetime

    @classmethod
    def from_model(cls, invoice: Invoice) -> Self:
        quote = invoice.quote
        summary = InvoiceSummary.from_model(invoice)
        return cls(
            **summary.model_dump(),
            client=ClientDetails(
                name=quote.client_name,
                phone=quote.client_phone,
                email=quote.client_email,
            ),
            paid_at=invoice.paid_at,
            tax_label=quote.tax_label,
            tax_rate_percent=quote.tax_rate_percent,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            deposit_amount=invoice.deposit_amount,
            amount_paid=invoice.amount_paid,
            payment_link=invoice.payment_link,
            notes=invoice.notes,
            terms=invoice.terms,
            lines=[QuoteLineRead.model_validate(line) for line in quote.lines],
            updated_at=invoice.updated_at,
        )
