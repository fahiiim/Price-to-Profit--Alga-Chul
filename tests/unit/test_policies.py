from decimal import Decimal as D

import pytest

from app.invoices.policy import InvoiceStatus, amount_paid_for
from app.library.rules import missing_fields, unrelated_fields
from app.pricing.enums import LineKind
from app.quotes.policy import QuoteStatus, can_be_invoiced, can_transition


@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        (QuoteStatus.DRAFT, QuoteStatus.SENT, True),
        (QuoteStatus.SENT, QuoteStatus.ACCEPTED, True),
        (QuoteStatus.DECLINED, QuoteStatus.ACCEPTED, False),
        (QuoteStatus.ACCEPTED, QuoteStatus.DRAFT, False),
        (QuoteStatus.INVOICED, QuoteStatus.DRAFT, False),
        (QuoteStatus.DRAFT, QuoteStatus.INVOICED, False),
    ],
)
def test_quote_transitions(
    current: QuoteStatus, target: QuoteStatus, allowed: bool
) -> None:
    assert can_transition(current, target) is allowed


def test_only_open_quotes_can_be_invoiced() -> None:
    assert can_be_invoiced(QuoteStatus.ACCEPTED)
    assert not can_be_invoiced(QuoteStatus.DECLINED)
    assert not can_be_invoiced(QuoteStatus.INVOICED)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (InvoiceStatus.UNPAID, D("0")),
        (InvoiceStatus.DEPOSIT_PAID, D("600")),
        (InvoiceStatus.PAID, D("2104")),
    ],
)
def test_amount_paid_follows_status(status: InvoiceStatus, expected: D) -> None:
    paid = amount_paid_for(status, total=D("2104"), deposit_amount=D("600"))
    assert paid == expected


def test_library_rules_per_kind() -> None:
    assert missing_fields(LineKind.HAIR, {"pack_price": D("1")}) == ["grams_per_pack"]
    assert missing_fields(LineKind.LABOUR, {}) == []
    assert "unit_price" in unrelated_fields(LineKind.HAIR)
    assert "pack_price" not in unrelated_fields(LineKind.HAIR)
