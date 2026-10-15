from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.core.schemas import Grams, MarkupPercent, Money
from app.library.rules import missing_fields
from app.pricing.enums import LineKind
from app.pricing.money import round_rate

KIND_HELP = (
    "`hair` needs `grams_per_pack` and `pack_price` (optional `markup_percent`). "
    "`labour` can set `hourly_rate` (otherwise the business rate is used). "
    "`service`, `material` and `fee` need `unit_price` "
    "(optional `unit_cost` and `unit_label`)."
)


class LibraryItemFields(BaseModel):
    """Descriptive and pricing fields shared by create and read schemas."""

    name: str = Field(
        min_length=1, max_length=120, examples=["Russian tape-ins 20in, #60"]
    )
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(
        default=None,
        max_length=60,
        description="Free-text group used to organise the library.",
        examples=["Tape-ins"],
    )
    taxable: bool = Field(
        default=True, description="Whether VAT applies when this item is quoted."
    )
    grams_per_pack: Grams | None = Field(
        default=None, description="Hair only: grams in one pack.", examples=["100"]
    )
    pack_price: Money | None = Field(
        default=None,
        description="Hair only: what one pack costs you.",
        examples=["350.00"],
    )
    markup_percent: MarkupPercent | None = Field(
        default=None,
        description="Hair only: markup for this product. Null uses the business "
        "default markup.",
    )
    hourly_rate: Money | None = Field(
        default=None,
        description="Labour only: price per hour. Null uses the business rate.",
    )
    unit_price: Money | None = Field(
        default=None,
        description="Service, material or fee: price charged per unit.",
        examples=["80.00"],
    )
    unit_cost: Money | None = Field(
        default=None,
        description="Service, material or fee: what one unit costs you.",
        examples=["40.00"],
    )
    unit_label: str | None = Field(
        default=None, max_length=20, examples=["pack", "bottle"]
    )


class LibraryItemCreate(LibraryItemFields):
    """A new library item. `kind` decides which pricing fields are required."""

    kind: LineKind = Field(description=KIND_HELP)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "kind": "hair",
                    "name": "Russian tape-ins 20in, #60",
                    "category": "Tape-ins",
                    "grams_per_pack": "100",
                    "pack_price": "350.00",
                },
                {
                    "kind": "material",
                    "name": "Tape tabs and remover",
                    "unit_price": "80.00",
                    "unit_cost": "40.00",
                },
            ]
        }
    )

    @model_validator(mode="after")
    def _check_kind_fields(self) -> Self:
        missing = missing_fields(self.kind, self.model_dump())
        if missing:
            raise ValueError(f"`{self.kind}` items require: {', '.join(missing)}.")
        return self


class LibraryItemUpdate(BaseModel):
    """Partial update. Only the fields you send are changed.

    Changing `kind` clears the pricing fields that no longer apply.
    """

    kind: LineKind | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=60)
    taxable: bool | None = None
    is_archived: bool | None = Field(
        default=None, description="Archived items are hidden from the picker."
    )
    grams_per_pack: Grams | None = None
    pack_price: Money | None = None
    markup_percent: MarkupPercent | None = None
    hourly_rate: Money | None = None
    unit_price: Money | None = None
    unit_cost: Money | None = None
    unit_label: str | None = Field(default=None, max_length=20)


class LibraryItemRead(LibraryItemFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: LineKind
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    @computed_field(description="Hair only: pack price / grams per pack.")
    @property
    def cost_per_gram(self) -> Decimal | None:
        if self.grams_per_pack and self.pack_price is not None:
            return round_rate(self.pack_price / self.grams_per_pack)
        return None
