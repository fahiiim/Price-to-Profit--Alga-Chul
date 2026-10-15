from typing import Annotated

from fastapi import APIRouter, Body, Query, Response, status

from app.business.dependencies import CurrentBusiness
from app.core.dependencies import PaginationDep, SessionDep
from app.core.schemas import Page, error_responses
from app.invoices.policy import InvoiceStatus
from app.invoices.schemas import (
    InvoiceCreate,
    InvoiceRead,
    InvoiceStatusUpdate,
    InvoiceSummary,
)
from app.invoices.service import (
    change_invoice_status,
    create_invoice,
    delete_invoice,
    get_invoice,
    list_invoices,
)
from app.quotes.service import get_quote

router = APIRouter(tags=["Invoices"], responses=error_responses(422))


@router.post(
    "/quotes/{quote_id}/invoice",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invoice from a quote",
    description=(
        "Turns a `draft`, `sent` or `accepted` quote into an invoice with the "
        "next invoice number (e.g. `INV-0001`). The quote becomes `invoiced` "
        "and is locked against edits.\n\n"
        "Totals, the payment link and the invoice terms are copied at this "
        "moment. Returns **409** if the quote already has an invoice or is "
        "`declined`."
    ),
    response_description="The new invoice.",
    responses=error_responses(404, 409),
)
def create_invoice_for_quote(
    quote_id: int,
    response: Response,
    business: CurrentBusiness,
    session: SessionDep,
    payload: Annotated[InvoiceCreate | None, Body()] = None,
) -> InvoiceRead:
    quote = get_quote(session, business, quote_id)
    invoice = create_invoice(session, business, quote, payload or InvoiceCreate())
    response.headers["Location"] = f"/v1/invoices/{invoice.id}"
    return InvoiceRead.from_model(invoice)


@router.get(
    "/invoices",
    response_model=Page[InvoiceSummary],
    summary="List invoices",
    description="Newest issue date first. Filter by payment status or search.",
    response_description="A page of invoice summaries.",
)
def list_all_invoices(
    business: CurrentBusiness,
    session: SessionDep,
    pagination: PaginationDep,
    status_filter: Annotated[
        InvoiceStatus | None,
        Query(alias="status", description="Only invoices with this status."),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            max_length=100,
            description="Match invoice number, quote number or client name.",
        ),
    ] = None,
) -> Page[InvoiceSummary]:
    invoices, total = list_invoices(
        session,
        business,
        status=status_filter,
        search=search,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[InvoiceSummary](
        items=[InvoiceSummary.from_model(invoice) for invoice in invoices],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceRead,
    summary="Get an invoice",
    description="Returns the invoice with its client, lines and payment state.",
    response_description="The invoice.",
    responses=error_responses(404),
)
def get_single_invoice(
    invoice_id: int, business: CurrentBusiness, session: SessionDep
) -> InvoiceRead:
    return InvoiceRead.from_model(get_invoice(session, business, invoice_id))


@router.patch(
    "/invoices/{invoice_id}/status",
    response_model=InvoiceRead,
    summary="Record a payment",
    description=(
        "Sets the payment status. `amount_paid` and `amount_due` follow it:\n\n"
        "| status | amount_paid |\n"
        "| --- | --- |\n"
        "| `unpaid` | 0 |\n"
        "| `deposit_paid` | the quote deposit |\n"
        "| `paid` | the total (also sets `paid_at`) |"
    ),
    response_description="The invoice with its new payment status.",
    responses=error_responses(404),
)
def update_invoice_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    business: CurrentBusiness,
    session: SessionDep,
) -> InvoiceRead:
    invoice = get_invoice(session, business, invoice_id)
    return InvoiceRead.from_model(
        change_invoice_status(session, invoice, payload.status)
    )


@router.delete(
    "/invoices/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an invoice",
    description=(
        "Deletes the invoice and moves its quote back to `accepted`, so the "
        "quote can be edited and invoiced again. The invoice number is not "
        "reused."
    ),
    responses=error_responses(404),
)
def delete_existing_invoice(
    invoice_id: int, business: CurrentBusiness, session: SessionDep
) -> None:
    delete_invoice(session, get_invoice(session, business, invoice_id))
