"""Price individual quote lines and calculate quote totals.

Rounding policy: every line's price and cost are rounded to two decimals first,
then totals are summed from the rounded lines. VAT is rounded once, on the
taxable subtotal. This keeps the PDF columns adding up exactly.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.pricing.enums import DepositMode
from app.pricing.errors import PricingError
from app.pricing.money import HUNDRED, ZERO, percent_of, round_money, round_rate


@dataclass(frozen=True, slots=True)
class HairLine:
    """Hair sold by weight and bought from the supplier in packs."""

    grams_required: Decimal
    grams_per_pack: Decimal
    pack_price: Decimal
    markup_percent: Decimal
    whole_packs: bool = True
    taxable: bool = True


@dataclass(frozen=True, slots=True)
class LabourLine:
    """Time charged by the hour. Counts toward profit per hour."""

    hours: Decimal
    hourly_rate: Decimal
    taxable: bool = True


@dataclass(frozen=True, slots=True)
class ItemLine:
    """A fixed-price service, material or fee, optionally with a cost."""

    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal = ZERO
    taxable: bool = True


type LineInput = HairLine | LabourLine | ItemLine


@dataclass(frozen=True, slots=True)
class LineResult:
    """What one line charges the client and costs the stylist."""

    price: Decimal
    cost: Decimal
    taxable: bool
    hours: Decimal = ZERO
    cost_per_gram: Decimal | None = None
    packs_needed: int | None = None
    leftover_grams: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Deposit:
    mode: DepositMode
    value: Decimal


@dataclass(frozen=True, slots=True)
class QuoteTotals:
    subtotal: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    deposit_amount: Decimal
    balance_due: Decimal
    total_cost: Decimal
    profit: Decimal
    labour_hours: Decimal
    profit_per_hour: Decimal | None
    margin_percent: Decimal | None


@dataclass(frozen=True, slots=True)
class PricedQuote:
    lines: tuple[LineResult, ...]
    totals: QuoteTotals


def price_hair(line: HairLine) -> LineResult:
    """Price hair, buying whole packs unless `whole_packs` is false.

    Whole packs: packs = ceil(required / pack size), cost = packs x pack price,
    and the unused grams are reported as leftover. Otherwise the cost is
    required grams x cost per gram. The selling price is cost plus markup.
    """
    _ensure_positive(line.grams_required, "grams_required")
    _ensure_positive(line.grams_per_pack, "grams_per_pack")
    _ensure_non_negative(line.pack_price, "pack_price")
    _ensure_non_negative(line.markup_percent, "markup_percent")

    cost_per_gram = line.pack_price / line.grams_per_pack
    packs_needed = math.ceil(line.grams_required / line.grams_per_pack)
    if line.whole_packs:
        cost = line.pack_price * packs_needed
        leftover = line.grams_per_pack * packs_needed - line.grams_required
    else:
        cost = cost_per_gram * line.grams_required
        leftover = ZERO

    cost = round_money(cost)
    price = round_money(cost + percent_of(cost, line.markup_percent))
    return LineResult(
        price=price,
        cost=cost,
        taxable=line.taxable,
        cost_per_gram=round_rate(cost_per_gram),
        packs_needed=packs_needed,
        leftover_grams=round_money(leftover),
    )


def price_labour(line: LabourLine) -> LineResult:
    """Price hourly work: hours x hourly rate. Labour has no direct cost."""
    _ensure_positive(line.hours, "hours")
    _ensure_non_negative(line.hourly_rate, "hourly_rate")
    return LineResult(
        price=round_money(line.hours * line.hourly_rate),
        cost=ZERO,
        taxable=line.taxable,
        hours=line.hours,
    )


def price_item(line: ItemLine) -> LineResult:
    """Price a service, material or fee: quantity x unit price (and cost)."""
    _ensure_positive(line.quantity, "quantity")
    _ensure_non_negative(line.unit_price, "unit_price")
    _ensure_non_negative(line.unit_cost, "unit_cost")
    return LineResult(
        price=round_money(line.quantity * line.unit_price),
        cost=round_money(line.quantity * line.unit_cost),
        taxable=line.taxable,
    )


def price_line(line: LineInput) -> LineResult:
    """Price any supported line."""
    match line:
        case HairLine():
            return price_hair(line)
        case LabourLine():
            return price_labour(line)
        case ItemLine():
            return price_item(line)
    raise PricingError(f"Unsupported line type: {type(line).__name__}.")


def calculate_deposit(total: Decimal, deposit: Deposit | None) -> Decimal:
    """Return the deposit for `total`, never more than the total itself."""
    if deposit is None:
        return ZERO
    _ensure_non_negative(deposit.value, "deposit.value")
    if deposit.mode is DepositMode.PERCENT:
        _ensure_at_most(deposit.value, HUNDRED, "deposit.value")
        amount = round_money(percent_of(total, deposit.value))
    else:
        amount = round_money(deposit.value)
    return min(amount, total)


def calculate_totals(
    lines: Sequence[LineResult],
    *,
    tax_rate_percent: Decimal,
    deposit: Deposit | None = None,
) -> QuoteTotals:
    """Combine priced lines into the quote totals.

    total = subtotal + tax; balance = total - deposit;
    profit = total - tax - costs (equal to subtotal - costs);
    profit per hour = profit / labour hours.
    """
    _ensure_non_negative(tax_rate_percent, "tax_rate_percent")
    _ensure_at_most(tax_rate_percent, HUNDRED, "tax_rate_percent")

    subtotal = sum((line.price for line in lines), ZERO)
    taxable_amount = sum((line.price for line in lines if line.taxable), ZERO)
    tax_amount = round_money(percent_of(taxable_amount, tax_rate_percent))
    total = subtotal + tax_amount
    deposit_amount = calculate_deposit(total, deposit)
    total_cost = sum((line.cost for line in lines), ZERO)
    labour_hours = sum((line.hours for line in lines), ZERO)
    profit = subtotal - total_cost

    profit_per_hour = round_money(profit / labour_hours) if labour_hours else None
    margin_percent = round_money(profit / subtotal * HUNDRED) if subtotal else None
    return QuoteTotals(
        subtotal=subtotal,
        taxable_amount=taxable_amount,
        tax_amount=tax_amount,
        total=total,
        deposit_amount=deposit_amount,
        balance_due=total - deposit_amount,
        total_cost=total_cost,
        profit=profit,
        labour_hours=labour_hours,
        profit_per_hour=profit_per_hour,
        margin_percent=margin_percent,
    )


def price_quote(
    lines: Sequence[LineInput],
    *,
    tax_rate_percent: Decimal,
    deposit: Deposit | None = None,
) -> PricedQuote:
    """Price every line, then calculate the totals."""
    results = tuple(price_line(line) for line in lines)
    totals = calculate_totals(
        results, tax_rate_percent=tax_rate_percent, deposit=deposit
    )
    return PricedQuote(lines=results, totals=totals)


def _ensure_positive(value: Decimal, name: str) -> None:
    if value <= ZERO:
        raise PricingError(f"`{name}` must be greater than 0.")


def _ensure_non_negative(value: Decimal, name: str) -> None:
    if value < ZERO:
        raise PricingError(f"`{name}` cannot be negative.")


def _ensure_at_most(value: Decimal, limit: Decimal, name: str) -> None:
    if value > limit:
        raise PricingError(f"`{name}` cannot be more than {limit}.")
