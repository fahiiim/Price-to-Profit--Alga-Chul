"""Decimal helpers. Money is always rounded half-up to two decimal places."""

from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
HUNDRED = Decimal("100")
CENT = Decimal("0.01")
RATE_QUANTUM = Decimal("0.0001")


def round_money(value: Decimal) -> Decimal:
    """Round to two decimals, half-up (2.345 -> 2.35)."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def round_rate(value: Decimal) -> Decimal:
    """Round a unit rate, such as cost per gram, to four decimals."""
    return value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)


def percent_of(amount: Decimal, percent: Decimal) -> Decimal:
    """Return `percent` % of `amount`, unrounded."""
    return amount * percent / HUNDRED
