"""Turn numbers and dates into the text printed on documents."""

from datetime import date
from decimal import Decimal

MULTIPLICATION_SIGN = "\u00d7"


def money(value: Decimal, currency: str | None = None) -> str:
    """`money(Decimal("2104"), "AED")` -> `"AED 2,104.00"`."""
    amount = f"{value:,.2f}"
    return f"{currency} {amount}" if currency else amount


def quantity(value: Decimal) -> str:
    """Print without trailing zeros: 3.50 -> "3.5", 170.00 -> "170"."""
    text = f"{value:,.2f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def times(count: str, rate: str) -> str:
    """Join a count and a rate with a multiplication sign: "3.5 h x 180.00"."""
    return f"{count} {MULTIPLICATION_SIGN} {rate}"


def percent(value: Decimal) -> str:
    return f"{quantity(value)}%"


def long_date(value: date) -> str:
    """`date(2026, 11, 2)` -> `"2 Nov 2026"`."""
    return f"{value.day} {value:%b %Y}"
