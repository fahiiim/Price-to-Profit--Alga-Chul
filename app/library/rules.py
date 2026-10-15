"""Which pricing fields belong to which kind of library item."""

from collections.abc import Mapping

from app.pricing.enums import LineKind

_ITEM_FIELDS = ("unit_price", "unit_cost", "unit_label")

KIND_FIELDS: dict[LineKind, tuple[str, ...]] = {
    LineKind.HAIR: ("grams_per_pack", "pack_price", "markup_percent"),
    LineKind.LABOUR: ("hourly_rate",),
    LineKind.SERVICE: _ITEM_FIELDS,
    LineKind.MATERIAL: _ITEM_FIELDS,
    LineKind.FEE: _ITEM_FIELDS,
}
"""Pricing fields that are meaningful for each kind."""

REQUIRED_KIND_FIELDS: dict[LineKind, tuple[str, ...]] = {
    LineKind.HAIR: ("grams_per_pack", "pack_price"),
    LineKind.LABOUR: (),
    LineKind.SERVICE: ("unit_price",),
    LineKind.MATERIAL: ("unit_price",),
    LineKind.FEE: ("unit_price",),
}
"""Pricing fields that must be set for each kind.

Labour has none: without its own `hourly_rate` it uses the business rate.
"""

PRICING_FIELDS = frozenset(name for names in KIND_FIELDS.values() for name in names)


def missing_fields(kind: LineKind, values: Mapping[str, object]) -> list[str]:
    """Required fields for `kind` that are absent or null in `values`."""
    return [name for name in REQUIRED_KIND_FIELDS[kind] if values.get(name) is None]


def unrelated_fields(kind: LineKind) -> frozenset[str]:
    """Pricing fields that do not apply to `kind` and should be cleared."""
    return PRICING_FIELDS - set(KIND_FIELDS[kind])
