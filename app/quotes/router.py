from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.business.dependencies import CurrentBusiness
from app.core.dependencies import PaginationDep, SessionDep
from app.core.schemas import Page, error_responses
from app.quotes.policy import QuoteStatus
from app.quotes.schemas import (
    QuoteCreate,
    QuotePreviewRead,
    QuotePreviewRequest,
    QuoteRead,
    QuoteStatusUpdate,
    QuoteSummary,
    QuoteUpdate,
)
from app.quotes.service import (
    QuoteFilters,
    change_quote_status,
    create_quote,
    delete_quote,
    duplicate_quote,
    get_quote,
    list_quotes,
    preview_quote,
    update_quote,
)

router = APIRouter(
    prefix="/quotes",
    tags=["Quotes"],
    responses=error_responses(401, 422),
)


@router.post(
    "/preview",
    response_model=QuotePreviewRead,
    summary="Price lines without saving",
    description=(
        "Runs the full pricing engine and returns every line's price and cost "
        "plus the totals. Nothing is saved. The quote builder calls this as "
        "the stylist types, so the totals bar updates live.\n\n"
        "The example request is the worked example from the spec. It returns "
        "subtotal **2,005.00**, VAT **99.00**, total **2,104.00**, balance "
        "**1,504.00**, profit **1,240.00** and **354.29** per hour."
    ),
    response_description="Priced lines and totals.",
    responses=error_responses(404),
)
def preview_quote_pricing(
    payload: QuotePreviewRequest, business: CurrentBusiness, session: SessionDep
) -> QuotePreviewRead:
    return preview_quote(session, business, payload)


@router.get(
    "",
    response_model=Page[QuoteSummary],
    summary="List quotes",
    description=(
        "Newest first. Combine `status`, `search` and the created-date range "
        "to power the Quotes history screen."
    ),
    response_description="A page of quote summaries.",
)
def list_all_quotes(
    business: CurrentBusiness,
    session: SessionDep,
    pagination: PaginationDep,
    status_filter: Annotated[
        QuoteStatus | None,
        Query(alias="status", description="Only quotes with this status."),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            max_length=100,
            description="Match quote number, client name, phone or title.",
        ),
    ] = None,
    created_from: Annotated[
        date | None, Query(description="Created on or after this date (UTC).")
    ] = None,
    created_to: Annotated[
        date | None, Query(description="Created on or before this date (UTC).")
    ] = None,
) -> Page[QuoteSummary]:
    filters = QuoteFilters(
        status=status_filter,
        search=search,
        created_from=created_from,
        created_to=created_to,
    )
    quotes, total = list_quotes(
        session,
        business,
        filters,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[QuoteSummary](
        items=[QuoteSummary.from_model(quote) for quote in quotes],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "",
    response_model=QuoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a quote",
    description=(
        "Prices the lines and saves a new `draft` quote with the next quote "
        "number (e.g. `Q-0001`).\n\n"
        "Currency, tax rate and deposit are copied onto the quote, so later "
        "changes to the business profile never change this quote."
    ),
    response_description="The saved quote with priced lines and totals.",
    responses=error_responses(404),
)
def create_new_quote(
    payload: QuoteCreate,
    response: Response,
    business: CurrentBusiness,
    session: SessionDep,
) -> QuoteRead:
    quote = create_quote(session, business, payload)
    response.headers["Location"] = f"/v1/quotes/{quote.id}"
    return QuoteRead.from_model(quote)


@router.get(
    "/{quote_id}",
    response_model=QuoteRead,
    summary="Get a quote",
    description="Returns the quote with its lines, totals and profit figures.",
    response_description="The quote.",
    responses=error_responses(404),
)
def get_single_quote(
    quote_id: int, business: CurrentBusiness, session: SessionDep
) -> QuoteRead:
    return QuoteRead.from_model(get_quote(session, business, quote_id))


@router.patch(
    "/{quote_id}",
    response_model=QuoteRead,
    summary="Update a quote",
    description=(
        "Partially updates a quote. Sending `lines` replaces all lines. "
        "Changing `lines`, `deposit` or `tax_rate_percent` re-prices it.\n\n"
        "Returns **409** if the quote is already invoiced."
    ),
    response_description="The updated quote.",
    responses=error_responses(404, 409),
)
def update_existing_quote(
    quote_id: int,
    payload: QuoteUpdate,
    business: CurrentBusiness,
    session: SessionDep,
) -> QuoteRead:
    quote = get_quote(session, business, quote_id)
    return QuoteRead.from_model(update_quote(session, business, quote, payload))


@router.patch(
    "/{quote_id}/status",
    response_model=QuoteRead,
    summary="Change a quote's status",
    description=(
        "Moves the quote through its lifecycle:\n\n"
        "| from | allowed targets |\n"
        "| --- | --- |\n"
        "| `draft` | `sent`, `accepted`, `declined` |\n"
        "| `sent` | `draft`, `accepted`, `declined` |\n"
        "| `accepted` | `sent`, `declined` |\n"
        "| `declined` | `draft`, `sent` |\n"
        "| `invoiced` | none (locked) |\n\n"
        "A quote becomes `invoiced` only through **Create an invoice**. "
        "Sending the current status is a no-op."
    ),
    response_description="The quote with its new status.",
    responses=error_responses(404, 409),
)
def update_quote_status(
    quote_id: int,
    payload: QuoteStatusUpdate,
    business: CurrentBusiness,
    session: SessionDep,
) -> QuoteRead:
    quote = get_quote(session, business, quote_id)
    return QuoteRead.from_model(change_quote_status(session, quote, payload.status))


@router.post(
    "/{quote_id}/duplicate",
    response_model=QuoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate a quote",
    description=(
        "Copies the client, lines and pricing settings into a new `draft` "
        "with a new number. The appointment date is cleared and the validity "
        "date restarts from today."
    ),
    response_description="The new draft quote.",
    responses=error_responses(404),
)
def duplicate_existing_quote(
    quote_id: int,
    response: Response,
    business: CurrentBusiness,
    session: SessionDep,
) -> QuoteRead:
    source = get_quote(session, business, quote_id)
    copy = duplicate_quote(session, business, source)
    response.headers["Location"] = f"/v1/quotes/{copy.id}"
    return QuoteRead.from_model(copy)


@router.delete(
    "/{quote_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a quote",
    description=(
        "Permanently deletes the quote and its lines. Returns **409** if it "
        "has an invoice; delete the invoice first."
    ),
    responses=error_responses(404, 409),
)
def delete_existing_quote(
    quote_id: int, business: CurrentBusiness, session: SessionDep
) -> None:
    delete_quote(session, get_quote(session, business, quote_id))
