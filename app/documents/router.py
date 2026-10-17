from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.business.dependencies import CurrentBusiness
from app.core.dependencies import SessionDep, SettingsDep
from app.core.schemas import error_responses
from app.documents.service import (
    RenderedDocument,
    render_cost_sheet_pdf,
    render_invoice_pdf,
    render_quote_pdf,
)

router = APIRouter(tags=["Documents"], responses=error_responses(401, 404, 422))

PDF_RESPONSE = {
    200: {
        "content": {"application/pdf": {}},
        "description": "The PDF file.",
    }
}

DownloadParam = Annotated[
    bool,
    Query(
        description=(
            "`true` asks the browser to save the file (attachment). "
            "`false` opens it in place (inline)."
        )
    ),
]


@router.get(
    "/quotes/{quote_id}/pdf",
    response_class=Response,
    summary="Download the client quote PDF",
    description=(
        "The branded quote to send to the client: logo, business details, "
        "lines with amounts, subtotal, VAT, total, deposit and balance, the "
        "payment link, notes and terms.\n\n"
        "Costs, markup and profit are **never** printed on this document."
    ),
    responses=PDF_RESPONSE,
)
def download_quote_pdf(
    quote_id: int,
    business: CurrentBusiness,
    session: SessionDep,
    settings: SettingsDep,
    download: DownloadParam = False,
) -> Response:
    document = render_quote_pdf(session, business, quote_id, settings.media_dir)
    return _pdf_response(document, download=download)


@router.get(
    "/quotes/{quote_id}/cost-sheet/pdf",
    response_class=Response,
    summary="Download the internal cost sheet PDF",
    description=(
        "The stylist's private breakdown for a quote: cost, price and profit "
        "per line, hair packs and leftover grams, total cost, profit, profit "
        "per hour and margin. Marked **internal - do not share**."
    ),
    responses=PDF_RESPONSE,
)
def download_cost_sheet_pdf(
    quote_id: int,
    business: CurrentBusiness,
    session: SessionDep,
    settings: SettingsDep,
    download: DownloadParam = False,
) -> Response:
    document = render_cost_sheet_pdf(session, business, quote_id, settings.media_dir)
    return _pdf_response(document, download=download)


@router.get(
    "/invoices/{invoice_id}/pdf",
    response_class=Response,
    summary="Download the invoice PDF",
    description=(
        "The branded invoice: issue and due dates, quote reference, lines, "
        "totals, amount paid and amount due, payment status badge, payment "
        "link (while money is still due) and invoice terms."
    ),
    responses=PDF_RESPONSE,
)
def download_invoice_pdf(
    invoice_id: int,
    business: CurrentBusiness,
    session: SessionDep,
    settings: SettingsDep,
    download: DownloadParam = False,
) -> Response:
    document = render_invoice_pdf(session, business, invoice_id, settings.media_dir)
    return _pdf_response(document, download=download)


def _pdf_response(document: RenderedDocument, *, download: bool) -> Response:
    disposition = "attachment" if download else "inline"
    return Response(
        content=document.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{document.filename}"'
        },
    )
