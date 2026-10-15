"""Compose admin views from the feature services. No queries of its own."""

from sqlalchemy.orm import Session

from app.activity.schemas import ActivityRead
from app.activity.service import list_activity
from app.admin.schemas import AdminBusinessDetail, AdminOverview, BusinessSnapshot
from app.business.models import BusinessProfile
from app.business.schemas import BusinessRead
from app.core.clock import today
from app.dashboard.service import (
    compute_outstanding,
    compute_period_metrics,
    count_invoices_by_status,
    count_quotes_by_status,
)
from app.library.service import count_items_by_kind

RECENT_ACTIVITY_LIMIT = 10


def get_overview(session: Session, business: BusinessProfile) -> AdminOverview:
    end = today()
    activity, _ = list_activity(session, limit=RECENT_ACTIVITY_LIMIT)
    return AdminOverview(
        business=BusinessSnapshot(
            id=business.id,
            business_name=business.business_name,
            currency=business.currency,
            has_logo=business.logo_path is not None,
            created_at=business.created_at,
        ),
        this_month=compute_period_metrics(session, business, end.replace(day=1), end),
        all_time=compute_period_metrics(session, business, None, None),
        outstanding=compute_outstanding(session, business),
        quote_status_counts=count_quotes_by_status(session, business),
        invoice_status_counts=count_invoices_by_status(session, business),
        library_item_counts=count_items_by_kind(session, business),
        recent_activity=[ActivityRead.model_validate(entry) for entry in activity],
    )


def get_business_detail(
    session: Session, business: BusinessProfile
) -> AdminBusinessDetail:
    return AdminBusinessDetail(
        profile=BusinessRead.model_validate(business),
        usage=compute_period_metrics(session, business, None, None),
        outstanding=compute_outstanding(session, business),
        library_item_counts=count_items_by_kind(session, business),
    )
