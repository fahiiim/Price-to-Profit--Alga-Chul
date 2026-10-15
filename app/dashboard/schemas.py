from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.invoices.policy import InvoiceStatus
from app.quotes.policy import QuoteStatus
from app.quotes.schemas import QuoteSummary


class PeriodMetrics(BaseModel):
    """Figures for one date range. Null dates mean "no limit"."""

    date_from: date | None
    date_to: date | None
    quotes_created: int = Field(description="Quotes created in the period.")
    quoted_value: Decimal = Field(description="Sum of their totals.")
    quotes_won: int = Field(
        description="Quotes created in the period that are accepted or invoiced."
    )
    win_rate_percent: Decimal | None = Field(
        description="quotes_won / quotes_created x 100. Null with no quotes."
    )
    invoices_issued: int = Field(description="Invoices issued in the period.")
    invoiced_value: Decimal = Field(description="Sum of their totals.")
    collected: Decimal = Field(description="Amount paid on those invoices.")
    profit: Decimal = Field(description="Profit of the invoiced quotes.")
    labour_hours: Decimal = Field(description="Labour hours of the invoiced quotes.")
    profit_per_hour: Decimal | None = Field(
        description="profit / labour_hours. Null without labour."
    )


class OutstandingRead(BaseModel):
    """Money still owed on invoices that are not fully paid (all time)."""

    unpaid_invoices: int
    amount_due: Decimal


class DashboardRead(BaseModel):
    currency: str = Field(examples=["AED"])
    period: PeriodMetrics
    outstanding: OutstandingRead
    quote_status_counts: dict[QuoteStatus, int] = Field(
        description="All-time number of quotes in each status."
    )
    invoice_status_counts: dict[InvoiceStatus, int] = Field(
        description="All-time number of invoices in each status."
    )
    recent_quotes: list[QuoteSummary] = Field(
        description="The five most recently created quotes."
    )
