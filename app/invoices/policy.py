"""Invoice payment rules. Pure functions with no database or HTTP imports."""

from decimal import Decimal
from enum import StrEnum

from app.pricing.money import ZERO


class InvoiceStatus(StrEnum):
    UNPAID = "unpaid"
    """Nothing received yet."""

    DEPOSIT_PAID = "deposit_paid"
    """The deposit was received; the balance is still due."""

    PAID = "paid"
    """Paid in full."""


def amount_paid_for(
    status: InvoiceStatus, *, total: Decimal, deposit_amount: Decimal
) -> Decimal:
    """How much has been received for an invoice in `status`."""
    match status:
        case InvoiceStatus.PAID:
            return total
        case InvoiceStatus.DEPOSIT_PAID:
            return deposit_amount
    return ZERO
