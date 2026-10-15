"""Aggregate quote and invoice figures with SQL.

Money columns are stored as exact integers (see `ScaledDecimal`), so SQL sums
stay exact and come back as `Decimal`.
"""

from datetime import date, timedelta

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.business.models import BusinessProfile
from app.core.clock import today
from app.dashboard.schemas import DashboardRead, OutstandingRead, PeriodMetrics
from app.invoices.models import Invoice
from app.invoices.policy import InvoiceStatus
from app.pricing.money import HUNDRED, ZERO, round_money
from app.quotes.models import Quote
from app.quotes.policy import QuoteStatus
from app.quotes.schemas import QuoteSummary
from app.quotes.service import start_of_day

WON_STATUSES = (QuoteStatus.ACCEPTED, QuoteStatus.INVOICED)
RECENT_QUOTES_LIMIT = 5


def get_dashboard(
    session: Session,
    business: BusinessProfile,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> DashboardRead:
    """Home screen figures. Defaults to the current month so far."""
    if date_from is None and date_to is None:
        date_to = today()
        date_from = date_to.replace(day=1)

    recent = session.scalars(
        select(Quote)
        .where(Quote.business_id == business.id)
        .order_by(Quote.created_at.desc(), Quote.id.desc())
        .limit(RECENT_QUOTES_LIMIT)
    )
    return DashboardRead(
        currency=business.currency,
        period=compute_period_metrics(session, business, date_from, date_to),
        outstanding=compute_outstanding(session, business),
        quote_status_counts=count_quotes_by_status(session, business),
        invoice_status_counts=count_invoices_by_status(session, business),
        recent_quotes=[QuoteSummary.from_model(quote) for quote in recent],
    )


def compute_period_metrics(
    session: Session,
    business: BusinessProfile,
    date_from: date | None,
    date_to: date | None,
) -> PeriodMetrics:
    quote_filters = [Quote.business_id == business.id]
    if date_from is not None:
        quote_filters.append(Quote.created_at >= start_of_day(date_from))
    if date_to is not None:
        quote_filters.append(
            Quote.created_at < start_of_day(date_to + timedelta(days=1))
        )

    quotes_created, quoted_value = session.execute(
        select(func.count(Quote.id), _sum(Quote.total)).where(*quote_filters)
    ).one()
    quotes_won = (
        session.scalar(
            select(func.count(Quote.id)).where(
                *quote_filters, Quote.status.in_(WON_STATUSES)
            )
        )
        or 0
    )

    invoice_filters = [Invoice.business_id == business.id]
    if date_from is not None:
        invoice_filters.append(Invoice.issue_date >= date_from)
    if date_to is not None:
        invoice_filters.append(Invoice.issue_date <= date_to)

    invoices_issued, invoiced_value, collected, profit, labour_hours = session.execute(
        select(
            func.count(Invoice.id),
            _sum(Invoice.total),
            _sum(Invoice.amount_paid),
            _sum(Quote.profit),
            _sum(Quote.labour_hours),
        )
        .join(Invoice.quote)
        .where(*invoice_filters)
    ).one()

    return PeriodMetrics(
        date_from=date_from,
        date_to=date_to,
        quotes_created=quotes_created,
        quoted_value=quoted_value,
        quotes_won=quotes_won,
        win_rate_percent=(
            round_money(HUNDRED * quotes_won / quotes_created)
            if quotes_created
            else None
        ),
        invoices_issued=invoices_issued,
        invoiced_value=invoiced_value,
        collected=collected,
        profit=profit,
        labour_hours=labour_hours,
        profit_per_hour=round_money(profit / labour_hours) if labour_hours else None,
    )


def compute_outstanding(session: Session, business: BusinessProfile) -> OutstandingRead:
    count, total, paid = session.execute(
        select(
            func.count(Invoice.id), _sum(Invoice.total), _sum(Invoice.amount_paid)
        ).where(
            Invoice.business_id == business.id,
            Invoice.status != InvoiceStatus.PAID,
        )
    ).one()
    return OutstandingRead(unpaid_invoices=count, amount_due=total - paid)


def count_quotes_by_status(
    session: Session, business: BusinessProfile
) -> dict[QuoteStatus, int]:
    rows = session.execute(
        select(Quote.status, func.count(Quote.id))
        .where(Quote.business_id == business.id)
        .group_by(Quote.status)
    )
    counts = dict.fromkeys(QuoteStatus, 0)
    counts.update(rows.all())
    return counts


def count_invoices_by_status(
    session: Session, business: BusinessProfile
) -> dict[InvoiceStatus, int]:
    rows = session.execute(
        select(Invoice.status, func.count(Invoice.id))
        .where(Invoice.business_id == business.id)
        .group_by(Invoice.status)
    )
    counts = dict.fromkeys(InvoiceStatus, 0)
    counts.update(rows.all())
    return counts


def _sum(column: ColumnElement) -> ColumnElement:
    """SUM that returns 0 instead of NULL and keeps the column's Decimal type."""
    return func.coalesce(func.sum(column), ZERO, type_=column.type)
