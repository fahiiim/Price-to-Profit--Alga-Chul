"""Build `DocumentData` for each document type from saved records.

This is the only place that decides what a client sees and what stays
internal: client documents never show costs, markup or profit.
"""

from decimal import Decimal
from pathlib import Path

from app.business.models import BusinessProfile
from app.documents.data import (
    BusinessBlock,
    DocumentData,
    LabeledValue,
    LineTable,
    TextSection,
)
from app.documents.formatting import long_date, money, percent, quantity, times
from app.invoices.models import Invoice
from app.invoices.policy import InvoiceStatus
from app.pricing.enums import LineKind
from app.pricing.money import ZERO
from app.quotes.models import Quote, QuoteLine

ONE = Decimal(1)

INVOICE_BADGES = {
    InvoiceStatus.UNPAID: "UNPAID",
    InvoiceStatus.DEPOSIT_PAID: "DEPOSIT PAID",
    InvoiceStatus.PAID: "PAID",
}


def build_quote_document(
    business: BusinessProfile, quote: Quote, logo_path: Path | None
) -> DocumentData:
    """The client-facing quote."""
    meta = [LabeledValue("Date", long_date(quote.created_at.date()))]
    if quote.valid_until:
        meta.append(LabeledValue("Valid until", long_date(quote.valid_until)))
    if quote.appointment_date:
        meta.append(LabeledValue("Appointment", long_date(quote.appointment_date)))

    return DocumentData(
        title="Quote",
        number=quote.number,
        business=_business_block(business, logo_path),
        meta=tuple(meta),
        client_heading="Prepared for",
        client_lines=_client_lines(quote),
        table=_client_table(quote),
        amounts=(
            LabeledValue("Subtotal", money(quote.subtotal, quote.currency)),
            _tax_row(quote),
            LabeledValue("Total", money(quote.total, quote.currency), emphasis=True),
            LabeledValue("Deposit due", money(quote.deposit_amount, quote.currency)),
            LabeledValue("Balance due", money(quote.balance_due, quote.currency)),
        ),
        payment_link=business.payment_link if quote.deposit_amount else None,
        payment_label="Pay deposit online",
        sections=_sections(("Notes", quote.notes), ("Terms", business.quote_terms)),
    )


def build_invoice_document(
    business: BusinessProfile, invoice: Invoice, logo_path: Path | None
) -> DocumentData:
    """The client-facing invoice."""
    quote = invoice.quote
    amount_due = invoice.total - invoice.amount_paid
    currency = invoice.currency
    return DocumentData(
        title="Invoice",
        number=invoice.number,
        business=_business_block(business, logo_path),
        meta=(
            LabeledValue("Issue date", long_date(invoice.issue_date)),
            LabeledValue("Due date", long_date(invoice.due_date)),
            LabeledValue("Quote ref.", quote.number),
        ),
        client_heading="Bill to",
        client_lines=_client_lines(quote),
        table=_client_table(quote),
        amounts=(
            LabeledValue("Subtotal", money(invoice.subtotal, currency)),
            _tax_row(quote),
            LabeledValue("Total", money(invoice.total, currency)),
            LabeledValue("Paid to date", money(invoice.amount_paid, currency)),
            LabeledValue("Amount due", money(amount_due, currency), emphasis=True),
        ),
        badge=INVOICE_BADGES[invoice.status],
        payment_link=invoice.payment_link if amount_due else None,
        payment_label="Pay invoice online",
        sections=_sections(("Notes", invoice.notes), ("Terms", invoice.terms)),
    )


def build_cost_sheet_document(
    business: BusinessProfile, quote: Quote, logo_path: Path | None
) -> DocumentData:
    """The stylist's private breakdown of cost, price and profit."""
    currency = quote.currency
    profit_per_hour = (
        money(quote.profit_per_hour, currency)
        if quote.profit_per_hour is not None
        else "-"
    )
    margin = percent(quote.margin_percent) if quote.margin_percent is not None else "-"
    return DocumentData(
        title="Cost sheet",
        number=quote.number,
        business=_business_block(business, logo_path),
        meta=(
            LabeledValue("Date", long_date(quote.created_at.date())),
            LabeledValue("Status", quote.status.value.capitalize()),
        ),
        client_heading="Client",
        client_lines=_client_lines(quote),
        highlights=(
            LabeledValue("Revenue (ex. tax)", money(quote.subtotal, currency)),
            LabeledValue("Total cost", money(quote.total_cost, currency)),
            LabeledValue("Profit", money(quote.profit, currency), emphasis=True),
            LabeledValue("Profit / hour", profit_per_hour),
            LabeledValue("Margin", margin),
        ),
        table=LineTable(
            headers=("Item", "Breakdown", "Cost", "Price", "Profit"),
            rows=tuple(
                (
                    line.description,
                    _cost_breakdown(line),
                    money(line.cost),
                    money(line.price),
                    money(line.price - line.cost),
                )
                for line in quote.lines
            ),
            column_widths=(0.26, 0.38, 0.12, 0.12, 0.12),
            numeric_columns=frozenset({2, 3, 4}),
        ),
        amounts=(
            LabeledValue("Subtotal", money(quote.subtotal, currency)),
            _tax_row(quote, label_suffix="collected"),
            LabeledValue("Client pays", money(quote.total, currency)),
            LabeledValue("Total cost", money(quote.total_cost, currency)),
            LabeledValue("Profit", money(quote.profit, currency), emphasis=True),
            LabeledValue("Labour hours", quantity(quote.labour_hours)),
        ),
        badge="INTERNAL - DO NOT SHARE",
        sections=_sections(("Internal notes", quote.internal_notes)),
    )


def _business_block(business: BusinessProfile, logo_path: Path | None) -> BusinessBlock:
    contact = [
        business.tagline,
        business.phone,
        business.email,
        business.address,
        business.instagram,
        business.website,
    ]
    if business.tax_registration_number:
        contact.append(f"TRN {business.tax_registration_number}")
    return BusinessBlock(
        name=business.business_name,
        contact_lines=tuple(line for line in contact if line),
        logo_path=logo_path,
    )


def _client_lines(quote: Quote) -> tuple[str, ...]:
    lines = (quote.client_name, quote.client_phone, quote.client_email, quote.title)
    return tuple(line for line in lines if line)


def _client_table(quote: Quote) -> LineTable:
    return LineTable(
        headers=("Description", "Details", "Amount"),
        rows=tuple(
            (line.description, _client_detail(line, quote), money(line.price))
            for line in quote.lines
        ),
        column_widths=(0.5, 0.3, 0.2),
        numeric_columns=frozenset({2}),
    )


def _client_detail(line: QuoteLine, quote: Quote) -> str:
    """What the client may see about a line: never cost or markup."""
    match line.kind:
        case LineKind.HAIR:
            detail = f"{quantity(line.grams_required or ZERO)} g"
        case LineKind.LABOUR:
            detail = _labour_rate(line)
        case _:
            units = line.quantity or ONE
            detail = "" if units == ONE else _unit_rate(line)
    if not line.taxable:
        detail = f"{detail} (no {quote.tax_label})".strip()
    return detail


def _cost_breakdown(line: QuoteLine) -> str:
    match line.kind:
        case LineKind.HAIR:
            return _hair_breakdown(line)
        case LineKind.LABOUR:
            return f"{_labour_rate(line)}, no direct cost"
        case _:
            return f"{_unit_rate(line)}, cost {money(line.unit_cost or ZERO)} each"


def _labour_rate(line: QuoteLine) -> str:
    return times(f"{quantity(line.hours or ZERO)} h", money(line.hourly_rate or ZERO))


def _unit_rate(line: QuoteLine) -> str:
    return times(quantity(line.quantity or ONE), money(line.unit_price or ZERO))


def _hair_breakdown(line: QuoteLine) -> str:
    grams = quantity(line.grams_required or ZERO)
    if line.whole_packs:
        packs = line.packs_needed or 0
        label = "pack" if packs == 1 else "packs"
        bought = times(f"{packs} {label}", money(line.pack_price or ZERO))
    else:
        bought = f"{money(line.cost_per_gram or ZERO)} per g"
    parts = [f"{grams} g needed", bought, f"+{percent(line.markup_percent or ZERO)}"]
    if line.leftover_grams:
        parts.append(f"{quantity(line.leftover_grams)} g left over")
    return ", ".join(parts)


def _tax_row(quote: Quote, *, label_suffix: str = "") -> LabeledValue:
    label = f"{quote.tax_label} ({percent(quote.tax_rate_percent)})"
    if label_suffix:
        label = f"{label} {label_suffix}"
    return LabeledValue(label, money(quote.tax_amount, quote.currency))


def _sections(*pairs: tuple[str, str | None]) -> tuple[TextSection, ...]:
    return tuple(
        TextSection(heading, body.strip())
        for heading, body in pairs
        if body and body.strip()
    )
