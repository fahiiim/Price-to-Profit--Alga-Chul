"""Quote lifecycle rules. Pure functions with no database or HTTP imports."""

from enum import StrEnum


class QuoteStatus(StrEnum):
    DRAFT = "draft"
    """Being prepared. Not shared with the client yet."""

    SENT = "sent"
    """Shared with the client, waiting for an answer."""

    ACCEPTED = "accepted"
    """The client agreed to the price."""

    DECLINED = "declined"
    """The client said no."""

    INVOICED = "invoiced"
    """An invoice was created. The quote is now locked."""


ALLOWED_TRANSITIONS: dict[QuoteStatus, frozenset[QuoteStatus]] = {
    QuoteStatus.DRAFT: frozenset(
        {QuoteStatus.SENT, QuoteStatus.ACCEPTED, QuoteStatus.DECLINED}
    ),
    QuoteStatus.SENT: frozenset(
        {QuoteStatus.DRAFT, QuoteStatus.ACCEPTED, QuoteStatus.DECLINED}
    ),
    QuoteStatus.ACCEPTED: frozenset({QuoteStatus.SENT, QuoteStatus.DECLINED}),
    QuoteStatus.DECLINED: frozenset({QuoteStatus.DRAFT, QuoteStatus.SENT}),
    QuoteStatus.INVOICED: frozenset(),
}
"""Manual status changes. `invoiced` is only reached by creating an invoice."""

INVOICEABLE_STATUSES = frozenset(
    {QuoteStatus.DRAFT, QuoteStatus.SENT, QuoteStatus.ACCEPTED}
)


def can_transition(current: QuoteStatus, target: QuoteStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def is_editable(status: QuoteStatus) -> bool:
    """Invoiced quotes are locked so the invoice always matches its quote."""
    return status is not QuoteStatus.INVOICED


def can_be_invoiced(status: QuoteStatus) -> bool:
    return status in INVOICEABLE_STATUSES
