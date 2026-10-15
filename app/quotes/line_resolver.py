"""Turn incoming quote lines into pricing-engine inputs.

Each value is taken from the first place that has it: the line itself, the
linked library item, then the business defaults. Missing required values are
reported with the line number so the app can point at the right row.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.business.models import BusinessProfile
from app.core.errors import BusinessRuleError
from app.library.models import LibraryItem
from app.library.service import get_items_by_id
from app.pricing import (
    HairLine,
    ItemLine,
    LabourLine,
    LineInput,
    LineKind,
    LineResult,
)
from app.pricing.money import ZERO
from app.quotes.models import QuoteLine
from app.quotes.schemas import QuoteLineInput

DEFAULT_DESCRIPTIONS: dict[LineKind, str] = {
    LineKind.HAIR: "Hair",
    LineKind.LABOUR: "Installation",
    LineKind.SERVICE: "Service",
    LineKind.MATERIAL: "Materials",
    LineKind.FEE: "Fee",
}

RESULT_FIELDS = ("price", "cost", "cost_per_gram", "packs_needed", "leftover_grams")


@dataclass(frozen=True, slots=True)
class ResolvedLine:
    """A line with every value filled in, ready for the pricing engine."""

    kind: LineKind
    description: str
    library_item_id: int | None
    pricing_input: LineInput


def resolve_lines(
    session: Session,
    business: BusinessProfile,
    lines: Sequence[QuoteLineInput],
) -> list[ResolvedLine]:
    item_ids = [line.library_item_id for line in lines if line.library_item_id]
    items = get_items_by_id(session, business, item_ids)
    return [
        _resolve_line(position, line, items.get(line.library_item_id or 0), business)
        for position, line in enumerate(lines, start=1)
    ]


def resolve_saved_line(line: QuoteLine) -> ResolvedLine:
    """Rebuild a resolved line from a stored one, e.g. to duplicate a quote."""
    match line.kind:
        case LineKind.HAIR:
            pricing_input: LineInput = HairLine(
                grams_required=_stored(line.grams_required),
                grams_per_pack=_stored(line.grams_per_pack),
                pack_price=_stored(line.pack_price),
                markup_percent=_stored(line.markup_percent),
                whole_packs=bool(line.whole_packs),
                taxable=line.taxable,
            )
        case LineKind.LABOUR:
            pricing_input = LabourLine(
                hours=_stored(line.hours),
                hourly_rate=_stored(line.hourly_rate),
                taxable=line.taxable,
            )
        case _:
            pricing_input = ItemLine(
                quantity=_stored(line.quantity),
                unit_price=_stored(line.unit_price),
                unit_cost=_stored(line.unit_cost),
                taxable=line.taxable,
            )
    return ResolvedLine(
        kind=line.kind,
        description=line.description,
        library_item_id=line.library_item_id,
        pricing_input=pricing_input,
    )


def line_values(resolved: ResolvedLine, result: LineResult) -> dict[str, Any]:
    """Column values for a `QuoteLine` (or a preview line) from a priced line."""
    return {
        "kind": resolved.kind,
        "description": resolved.description,
        "library_item_id": resolved.library_item_id,
        **asdict(resolved.pricing_input),
        **{name: getattr(result, name) for name in RESULT_FIELDS},
    }


def _resolve_line(
    position: int,
    line: QuoteLineInput,
    item: LibraryItem | None,
    business: BusinessProfile,
) -> ResolvedLine:
    kind = line.kind or (item.kind if item else None)
    if kind is None:
        raise BusinessRuleError(
            f"Line {position}: `kind` is required when no library item is linked."
        )
    if item is not None and item.kind is not kind:
        raise BusinessRuleError(
            f"Line {position}: library item {item.id} is `{item.kind}`, not `{kind}`."
        )

    def pick(field: str, *fallbacks: Any) -> Any:
        return _first(getattr(line, field), _item_value(item, field), *fallbacks)

    def require(field: str) -> Decimal:
        value = pick(field)
        if value is None:
            raise BusinessRuleError(f"Line {position} ({kind}): `{field}` is required.")
        return value

    taxable = bool(pick("taxable", True))
    match kind:
        case LineKind.HAIR:
            pricing_input: LineInput = HairLine(
                grams_required=require("grams_required"),
                grams_per_pack=require("grams_per_pack"),
                pack_price=require("pack_price"),
                markup_percent=pick("markup_percent", business.default_markup_percent),
                whole_packs=bool(pick("whole_packs", business.whole_packs_default)),
                taxable=taxable,
            )
        case LineKind.LABOUR:
            pricing_input = LabourLine(
                hours=require("hours"),
                hourly_rate=pick("hourly_rate", business.hourly_rate),
                taxable=taxable,
            )
        case _:
            pricing_input = ItemLine(
                quantity=pick("quantity", Decimal(1)),
                unit_price=require("unit_price"),
                unit_cost=pick("unit_cost", ZERO),
                taxable=taxable,
            )

    description = _first(line.description, item.name if item else None)
    return ResolvedLine(
        kind=kind,
        description=description or DEFAULT_DESCRIPTIONS[kind],
        library_item_id=item.id if item else None,
        pricing_input=pricing_input,
    )


def _item_value(item: LibraryItem | None, field: str) -> Any:
    return getattr(item, field, None) if item is not None else None


def _first(*values: Any) -> Any:
    return next((value for value in values if value is not None), None)


def _stored(value: Decimal | None) -> Decimal:
    return value if value is not None else ZERO
