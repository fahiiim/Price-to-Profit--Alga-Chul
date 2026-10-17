"""Quote use cases. Each public function that writes owns one transaction."""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.activity.enums import ActivityAction
from app.activity.service import record_activity
from app.business.models import BusinessProfile
from app.business.service import allocate_quote_number
from app.core.clock import today, utc_now
from app.core.errors import ConflictError, NotFoundError
from app.pricing import Deposit, PricedQuote, price_quote
from app.quotes.line_resolver import (
    ResolvedLine,
    line_values,
    resolve_lines,
    resolve_saved_line,
)
from app.quotes.models import Quote, QuoteLine
from app.quotes.policy import QuoteStatus, can_transition, is_editable
from app.quotes.schemas import (
    ClientDetails,
    DepositInput,
    PricedLineRead,
    QuoteCreate,
    QuotePreviewRead,
    QuotePreviewRequest,
    QuoteTotalsRead,
    QuoteUpdate,
)

ENTITY_TYPE = "quote"
REPRICING_FIELDS = frozenset({"lines", "deposit", "tax_rate_percent"})
PLAIN_UPDATE_FIELDS = frozenset(
    {"title", "appointment_date", "valid_until", "notes", "internal_notes"}
)


@dataclass(frozen=True, slots=True)
class QuoteFilters:
    status: QuoteStatus | None = None
    search: str | None = None
    created_from: date | None = None
    created_to: date | None = None


def preview_quote(
    session: Session, business: BusinessProfile, payload: QuotePreviewRequest
) -> QuotePreviewRead:
    """Price lines with the same rules as a saved quote, without saving."""
    resolved = resolve_lines(session, business, payload.lines)
    deposit = payload.deposit or _business_deposit(business)
    tax_rate = _first_set(payload.tax_rate_percent, business.tax_rate_percent)
    priced = _price(resolved, tax_rate, deposit)
    return QuotePreviewRead(
        currency=business.currency,
        tax_label=business.tax_label,
        tax_rate_percent=tax_rate,
        deposit=deposit,
        lines=[
            PricedLineRead(**line_values(line, result))
            for line, result in zip(resolved, priced.lines, strict=True)
        ],
        totals=QuoteTotalsRead.model_validate(priced.totals),
    )


def list_quotes(
    session: Session,
    business: BusinessProfile,
    filters: QuoteFilters,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Quote], int]:
    statement = select(Quote).where(Quote.business_id == business.id)
    if filters.status is not None:
        statement = statement.where(Quote.status == filters.status)
    if filters.search:
        statement = statement.where(
            or_(
                Quote.number.icontains(filters.search, autoescape=True),
                Quote.client_name.icontains(filters.search, autoescape=True),
                Quote.client_phone.icontains(filters.search, autoescape=True),
                Quote.title.icontains(filters.search, autoescape=True),
            )
        )
    if filters.created_from is not None:
        statement = statement.where(
            Quote.created_at >= start_of_day(filters.created_from)
        )
    if filters.created_to is not None:
        statement = statement.where(
            Quote.created_at < start_of_day(filters.created_to + timedelta(days=1))
        )

    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    quotes = session.scalars(
        statement.order_by(Quote.created_at.desc(), Quote.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(quotes), total or 0


def get_quote(session: Session, business: BusinessProfile, quote_id: int) -> Quote:
    quote = session.scalar(
        select(Quote).where(Quote.id == quote_id, Quote.business_id == business.id)
    )
    if quote is None:
        raise NotFoundError(f"Quote {quote_id} was not found.")
    return quote


def create_quote(
    session: Session, business: BusinessProfile, payload: QuoteCreate
) -> Quote:
    resolved = resolve_lines(session, business, payload.lines)
    deposit = payload.deposit or _business_deposit(business)
    tax_rate = _first_set(payload.tax_rate_percent, business.tax_rate_percent)

    quote = Quote(
        business_id=business.id,
        number=allocate_quote_number(business),
        status=QuoteStatus.DRAFT,
        title=payload.title,
        appointment_date=payload.appointment_date,
        valid_until=payload.valid_until
        or today() + timedelta(days=business.quote_validity_days),
        notes=payload.notes,
        internal_notes=payload.internal_notes,
        currency=business.currency,
        tax_label=business.tax_label,
    )
    _set_client(quote, payload.client)
    _apply_pricing(quote, resolved, tax_rate, deposit)
    session.add(quote)
    session.flush()

    record_activity(
        session,
        action=ActivityAction.QUOTE_CREATED,
        entity_type=ENTITY_TYPE,
        entity_id=quote.id,
        summary=f"Quote {quote.number} created for {quote.client_name}",
        business_id=quote.business_id,
    )
    session.commit()
    return quote


def update_quote(
    session: Session,
    business: BusinessProfile,
    quote: Quote,
    payload: QuoteUpdate,
) -> Quote:
    _ensure_editable(quote)
    changes = payload.model_fields_set

    if payload.client is not None:
        _set_client(quote, payload.client)
    for field in PLAIN_UPDATE_FIELDS & changes:
        setattr(quote, field, getattr(payload, field))

    if changes & REPRICING_FIELDS:
        resolved = (
            resolve_lines(session, business, payload.lines)
            if payload.lines
            else [resolve_saved_line(line) for line in quote.lines]
        )
        deposit = payload.deposit or DepositInput(
            mode=quote.deposit_mode, value=quote.deposit_value
        )
        tax_rate = _first_set(payload.tax_rate_percent, quote.tax_rate_percent)
        _apply_pricing(quote, resolved, tax_rate, deposit)

    record_activity(
        session,
        action=ActivityAction.QUOTE_UPDATED,
        entity_type=ENTITY_TYPE,
        entity_id=quote.id,
        summary=f"Quote {quote.number} updated",
        business_id=quote.business_id,
    )
    session.commit()
    return quote


def change_quote_status(session: Session, quote: Quote, target: QuoteStatus) -> Quote:
    if target is quote.status:
        return quote
    if not can_transition(quote.status, target):
        raise ConflictError(
            f"Quote {quote.number} cannot move from `{quote.status}` to `{target}`."
        )

    previous = quote.status
    quote.status = target
    if target is QuoteStatus.SENT:
        quote.sent_at = utc_now()
    elif target is QuoteStatus.ACCEPTED:
        quote.accepted_at = utc_now()

    record_activity(
        session,
        action=ActivityAction.QUOTE_STATUS_CHANGED,
        entity_type=ENTITY_TYPE,
        entity_id=quote.id,
        summary=f"Quote {quote.number} moved from {previous} to {target}",
        business_id=quote.business_id,
    )
    session.commit()
    return quote


def duplicate_quote(
    session: Session, business: BusinessProfile, source: Quote
) -> Quote:
    """Copy a quote into a new draft with a new number, priced the same way."""
    copy = Quote(
        business_id=business.id,
        number=allocate_quote_number(business),
        status=QuoteStatus.DRAFT,
        title=source.title,
        client_name=source.client_name,
        client_phone=source.client_phone,
        client_email=source.client_email,
        appointment_date=None,
        valid_until=today() + timedelta(days=business.quote_validity_days),
        notes=source.notes,
        internal_notes=source.internal_notes,
        currency=source.currency,
        tax_label=source.tax_label,
    )
    resolved = [resolve_saved_line(line) for line in source.lines]
    deposit = DepositInput(mode=source.deposit_mode, value=source.deposit_value)
    _apply_pricing(copy, resolved, source.tax_rate_percent, deposit)
    session.add(copy)
    session.flush()

    record_activity(
        session,
        action=ActivityAction.QUOTE_DUPLICATED,
        entity_type=ENTITY_TYPE,
        entity_id=copy.id,
        summary=f"Quote {copy.number} duplicated from {source.number}",
        business_id=copy.business_id,
    )
    session.commit()
    return copy


def delete_quote(session: Session, quote: Quote) -> None:
    if quote.invoice is not None:
        raise ConflictError(
            f"Quote {quote.number} has an invoice. Delete the invoice first."
        )
    record_activity(
        session,
        action=ActivityAction.QUOTE_DELETED,
        entity_type=ENTITY_TYPE,
        entity_id=quote.id,
        summary=f"Quote {quote.number} for {quote.client_name} deleted",
        business_id=quote.business_id,
    )
    session.delete(quote)
    session.commit()


def start_of_day(day: date) -> datetime:
    """Midnight UTC at the start of `day`, for created-at range filters."""
    return datetime.combine(day, time.min, tzinfo=UTC)


def _apply_pricing(
    quote: Quote,
    resolved: Sequence[ResolvedLine],
    tax_rate_percent: Decimal,
    deposit: DepositInput,
) -> None:
    """Price the lines and store lines, settings and totals on the quote."""
    priced = _price(resolved, tax_rate_percent, deposit)
    quote.tax_rate_percent = tax_rate_percent
    quote.deposit_mode = deposit.mode
    quote.deposit_value = deposit.value
    quote.lines = [
        QuoteLine(position=position, **line_values(line, result))
        for position, (line, result) in enumerate(
            zip(resolved, priced.lines, strict=True), start=1
        )
    ]
    for name, value in asdict(priced.totals).items():
        setattr(quote, name, value)


def _price(
    resolved: Sequence[ResolvedLine],
    tax_rate_percent: Decimal,
    deposit: DepositInput,
) -> PricedQuote:
    return price_quote(
        [line.pricing_input for line in resolved],
        tax_rate_percent=tax_rate_percent,
        deposit=Deposit(mode=deposit.mode, value=deposit.value),
    )


def _business_deposit(business: BusinessProfile) -> DepositInput:
    return DepositInput(mode=business.deposit_mode, value=business.deposit_value)


def _set_client(quote: Quote, client: ClientDetails) -> None:
    quote.client_name = client.name
    quote.client_phone = client.phone
    quote.client_email = client.email


def _ensure_editable(quote: Quote) -> None:
    if not is_editable(quote.status):
        raise ConflictError(
            f"Quote {quote.number} is invoiced and can no longer be edited."
        )


def _first_set(value: Decimal | None, fallback: Decimal) -> Decimal:
    return fallback if value is None else value
