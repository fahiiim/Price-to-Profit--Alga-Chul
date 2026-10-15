"""Plain, already-formatted content for one PDF document."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BusinessBlock:
    name: str
    contact_lines: tuple[str, ...]
    logo_path: Path | None


@dataclass(frozen=True, slots=True)
class LabeledValue:
    """A label and its value, e.g. ("Total", "AED 2,104.00")."""

    label: str
    value: str
    emphasis: bool = False


@dataclass(frozen=True, slots=True)
class LineTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    column_widths: tuple[float, ...]
    """Fractions of the usable page width. Must add up to 1."""
    numeric_columns: frozenset[int] = frozenset()
    """Indexes of right-aligned columns."""


@dataclass(frozen=True, slots=True)
class TextSection:
    heading: str
    body: str


@dataclass(frozen=True, slots=True)
class DocumentData:
    title: str
    number: str
    business: BusinessBlock
    meta: tuple[LabeledValue, ...]
    client_heading: str
    client_lines: tuple[str, ...]
    table: LineTable
    amounts: tuple[LabeledValue, ...]
    highlights: tuple[LabeledValue, ...] = ()
    """Summary cards shown above the table (used by the cost sheet)."""
    badge: str | None = None
    """Short status label next to the title, e.g. "PAID"."""
    payment_link: str | None = None
    payment_label: str = "Pay online"
    sections: tuple[TextSection, ...] = field(default=())
