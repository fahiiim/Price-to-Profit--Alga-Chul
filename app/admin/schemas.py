from datetime import datetime

from pydantic import BaseModel, Field

from app.activity.schemas import ActivityRead
from app.business.schemas import BusinessRead
from app.dashboard.schemas import OutstandingRead, PeriodMetrics
from app.invoices.policy import InvoiceStatus
from app.pricing.enums import LineKind
from app.quotes.policy import QuoteStatus


class BusinessSnapshot(BaseModel):
    id: int
    business_name: str
    currency: str
    has_logo: bool
    created_at: datetime


class AdminOverview(BaseModel):
    """Everything on the admin Overview page in one request."""

    business: BusinessSnapshot
    this_month: PeriodMetrics
    all_time: PeriodMetrics
    outstanding: OutstandingRead
    quote_status_counts: dict[QuoteStatus, int]
    invoice_status_counts: dict[InvoiceStatus, int]
    library_item_counts: dict[LineKind, int] = Field(
        description="Active (not archived) library items per kind."
    )
    recent_activity: list[ActivityRead] = Field(
        description="The ten most recent changes."
    )


class AdminBusinessDetail(BaseModel):
    """The business profile together with its all-time usage."""

    profile: BusinessRead
    usage: PeriodMetrics
    outstanding: OutstandingRead
    library_item_counts: dict[LineKind, int]
