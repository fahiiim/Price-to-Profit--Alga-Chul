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


class PlatformOverview(BaseModel):
    totalSubscribers: int
    totalSubscribersChange: str
    active: int
    activeChange: str
    onTrial: int
    onTrialChange: str
    expired: int
    expiredChange: str
    quotesMonth: int
    quotesMonthChange: str
    estMrr: str
    estMrrChange: str
    monthlyPoints: list[dict] = Field(default_factory=list)
    dailyQuotes: list[dict] = Field(default_factory=list)
    planMix: dict = Field(default_factory=dict)
    topCountries: list[dict] = Field(default_factory=list)
    recentEvents: list[dict] = Field(default_factory=list)


class SubscriberItem(BaseModel):
    id: str
    initials: str
    name: str
    email: str
    phone: str
    owner: str
    country: str
    location: str
    instagram: str
    plan: str
    status: str
    joined: str
    quotesCount: int
    invoicesCount: int
    productsCount: int
    totalQuoted: str
    lastActive: str
    currency: str
    defaultVat: str
    defaultDeposit: str
    device: str
    appVersion: str
    internalNote: str = ""
    history: list[dict] = Field(default_factory=list)


class GrantFreePeriodRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)


class ToggleStatusRequest(BaseModel):
    disabled: bool


class UpdateNoteRequest(BaseModel):
    note: str = Field(..., max_length=1000)


class PlatformActivityItem(BaseModel):
    id: int
    time: str
    subscriber: str
    event: str
    details: str
    platform: str


class PlanTier(BaseModel):
    price: str
    period: str
    tag: str | None = None
    billingPeriod: str
    trialDays: int
    appStoreProductId: str
    features: list[str] = Field(default_factory=list)


class PaywallSettings(BaseModel):
    title: str
    subtitle: str
    badge: str
    benefits: list[str] = Field(default_factory=list)


class PlansConfigResponse(BaseModel):
    annual: PlanTier
    monthly: PlanTier
    paywall: PaywallSettings
