"""Invoice use cases. Each public function that writes owns one transaction."""

from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.activity.enums import ActivityAction
from app.activity.service import record_activity
from app.business.models import BusinessProfile
from app.business.service import allocate_invoice_number
from app.core.clock import today, utc_now
from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.invoices.models import Invoice
from app.invoices.policy import InvoiceStatus, amount_paid_for
from app.invoices.schemas import InvoiceCreate
from app.quotes.models import Quote
from app.quotes.policy import QuoteStatus, can_be_invoiced

ENTITY_TYPE = "invoice"


def create_invoice(
    session: Session,
    business: BusinessProfile,
    quote: Quote,
    payload: InvoiceCreate,
) -> Invoice:
    """Create the invoice for `quote` and lock the quote as `invoiced`."""
    if quote.invoice is not None:
        raise ConflictError(
            f"Quote {quote.number} already has invoice {quote.invoice.number}."
        )
    if not can_be_invoiced(quote.status):
        raise ConflictError(
            f"A `{quote.status}` quote cannot be invoiced. Move it back to "
            "`draft`, `sent` or `accepted` first."
        )

    issue_date = payload.issue_date or today()
    due_date = payload.due_date or issue_date + timedelta(
        days=business.invoice_due_days
    )
    if due_date < issue_date:
        raise BusinessRuleError("`due_date` cannot be before `issue_date`.")

    invoice = Invoice(
        business_id=business.id,
        quote=quote,
        number=allocate_invoice_number(business),
        status=InvoiceStatus.UNPAID,
        issue_date=issue_date,
        due_date=due_date,
        currency=quote.currency,
        subtotal=quote.subtotal,
        tax_amount=quote.tax_amount,
        total=quote.total,
        deposit_amount=quote.deposit_amount,
        amount_paid=amount_paid_for(
            InvoiceStatus.UNPAID,
            total=quote.total,
            deposit_amount=quote.deposit_amount,
        ),
        payment_link=business.payment_link,
        notes=payload.notes if payload.notes is not None else quote.notes,
        terms=business.invoice_terms,
    )
    quote.status = QuoteStatus.INVOICED
    session.add(invoice)
    session.flush()

    record_activity(
        session,
        action=ActivityAction.INVOICE_CREATED,
        entity_type=ENTITY_TYPE,
        entity_id=invoice.id,
        summary=f"Invoice {invoice.number} created from quote {quote.number}",
        business_id=invoice.business_id,
    )
    session.commit()
    return invoice


def list_invoices(
    session: Session,
    business: BusinessProfile,
    *,
    status: InvoiceStatus | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Invoice], int]:
    statement = (
        select(Invoice).join(Invoice.quote).where(Invoice.business_id == business.id)
    )
    if status is not None:
        statement = statement.where(Invoice.status == status)
    if search:
        statement = statement.where(
            or_(
                Invoice.number.icontains(search, autoescape=True),
                Quote.number.icontains(search, autoescape=True),
                Quote.client_name.icontains(search, autoescape=True),
            )
        )

    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    invoices = session.scalars(
        statement.order_by(Invoice.issue_date.desc(), Invoice.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(invoices), total or 0


def get_invoice(
    session: Session, business: BusinessProfile, invoice_id: int
) -> Invoice:
    invoice = session.scalar(
        select(Invoice).where(
            Invoice.id == invoice_id, Invoice.business_id == business.id
        )
    )
    if invoice is None:
        raise NotFoundError(f"Invoice {invoice_id} was not found.")
    return invoice


def change_invoice_status(
    session: Session, invoice: Invoice, target: InvoiceStatus
) -> Invoice:
    if target is invoice.status:
        return invoice

    previous = invoice.status
    invoice.status = target
    invoice.amount_paid = amount_paid_for(
        target, total=invoice.total, deposit_amount=invoice.deposit_amount
    )
    invoice.paid_at = utc_now() if target is InvoiceStatus.PAID else None

    record_activity(
        session,
        action=ActivityAction.INVOICE_STATUS_CHANGED,
        entity_type=ENTITY_TYPE,
        entity_id=invoice.id,
        summary=f"Invoice {invoice.number} moved from {previous} to {target}",
        business_id=invoice.business_id,
    )
    session.commit()
    return invoice


def delete_invoice(session: Session, invoice: Invoice) -> None:
    """Delete an invoice and unlock its quote (back to `accepted`)."""
    invoice.quote.status = QuoteStatus.ACCEPTED
    record_activity(
        session,
        action=ActivityAction.INVOICE_DELETED,
        entity_type=ENTITY_TYPE,
        entity_id=invoice.id,
        summary=(
            f"Invoice {invoice.number} deleted; quote {invoice.quote.number} "
            "is editable again"
        ),
        business_id=invoice.business_id,
    )
    session.delete(invoice)
    session.commit()
