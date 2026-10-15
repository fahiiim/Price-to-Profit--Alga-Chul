"""Load the records a document needs, build it and render it."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.business.models import BusinessProfile
from app.business.service import resolve_logo_path
from app.documents.builders import (
    build_cost_sheet_document,
    build_invoice_document,
    build_quote_document,
)
from app.documents.renderer import render_document
from app.invoices.service import get_invoice
from app.quotes.service import get_quote


@dataclass(frozen=True, slots=True)
class RenderedDocument:
    filename: str
    content: bytes


def render_quote_pdf(
    session: Session, business: BusinessProfile, quote_id: int, media_dir: Path
) -> RenderedDocument:
    quote = get_quote(session, business, quote_id)
    logo = resolve_logo_path(business, media_dir)
    return RenderedDocument(
        filename=f"{quote.number}.pdf",
        content=render_document(build_quote_document(business, quote, logo)),
    )


def render_cost_sheet_pdf(
    session: Session, business: BusinessProfile, quote_id: int, media_dir: Path
) -> RenderedDocument:
    quote = get_quote(session, business, quote_id)
    logo = resolve_logo_path(business, media_dir)
    return RenderedDocument(
        filename=f"{quote.number}-cost-sheet.pdf",
        content=render_document(build_cost_sheet_document(business, quote, logo)),
    )


def render_invoice_pdf(
    session: Session, business: BusinessProfile, invoice_id: int, media_dir: Path
) -> RenderedDocument:
    invoice = get_invoice(session, business, invoice_id)
    logo = resolve_logo_path(business, media_dir)
    return RenderedDocument(
        filename=f"{invoice.number}.pdf",
        content=render_document(build_invoice_document(business, invoice, logo)),
    )
