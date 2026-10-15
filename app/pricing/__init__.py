"""Pure pricing engine.

Nothing in this package imports FastAPI or SQLAlchemy, so every pricing rule
can be unit tested with plain values and reused by any caller.
"""

from app.pricing.calculator import (
    Deposit,
    HairLine,
    ItemLine,
    LabourLine,
    LineInput,
    LineResult,
    PricedQuote,
    QuoteTotals,
    calculate_deposit,
    calculate_totals,
    price_line,
    price_quote,
)
from app.pricing.enums import DepositMode, LineKind
from app.pricing.errors import PricingError

__all__ = [
    "Deposit",
    "DepositMode",
    "HairLine",
    "ItemLine",
    "LabourLine",
    "LineInput",
    "LineKind",
    "LineResult",
    "PricedQuote",
    "PricingError",
    "QuoteTotals",
    "calculate_deposit",
    "calculate_totals",
    "price_line",
    "price_quote",
]
