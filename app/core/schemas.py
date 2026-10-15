"""Schemas shared across features: errors, pagination and common field types."""

from decimal import Decimal
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, Field

from app.pricing.money import round_money

TwoDecimals = AfterValidator(round_money)
"""Normalise accepted input to two decimals, so `"200"` is stored and returned
as `"200.00"`. Values with more decimals are rejected before this runs."""

Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2), TwoDecimals]
"""A non-negative amount of money with two decimal places."""

Percent = Annotated[
    Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2), TwoDecimals
]
"""A percentage between 0 and 100, such as a VAT rate."""

MarkupPercent = Annotated[
    Decimal, Field(ge=0, le=1000, max_digits=6, decimal_places=2), TwoDecimals
]
"""A markup percentage. Can exceed 100 (a 150% markup is allowed)."""

Grams = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2), TwoDecimals]
"""A positive weight in grams."""

Hours = Annotated[
    Decimal, Field(gt=0, le=1000, max_digits=6, decimal_places=2), TwoDecimals
]
"""A positive number of working hours."""

Quantity = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2), TwoDecimals]
"""A positive quantity of units."""

HttpLink = Annotated[str, Field(max_length=500, pattern=r"^https?://\S+$")]
"""An absolute http(s) link."""


class ErrorDetail(BaseModel):
    location: list[str] = Field(
        description="Path to the invalid value, e.g. `['body', 'lines', 0]`."
    )
    message: str = Field(description="Human readable explanation.")
    type: str = Field(description="Machine readable validation error type.")


class ErrorBody(BaseModel):
    code: str = Field(
        description="Stable machine readable error code.",
        examples=["not_found"],
    )
    message: str = Field(
        description="Human readable explanation.",
        examples=["Quote 42 was not found."],
    )
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="Field level problems. Only present for `validation_error`.",
    )


class ErrorResponse(BaseModel):
    """The envelope returned by every failed request."""

    error: ErrorBody


class Page[ItemT](BaseModel):
    """One page of a list endpoint."""

    items: list[ItemT] = Field(description="Records on this page.")
    total: int = Field(description="Number of records matching the filters.")
    limit: int = Field(description="Page size that was applied.")
    offset: int = Field(description="Number of records skipped.")


_ERROR_DESCRIPTIONS: dict[int, str] = {
    404: "The resource does not exist.",
    409: "The request conflicts with the resource's current state.",
    413: "The uploaded file is too large.",
    415: "The uploaded file type is not supported.",
    422: "The request failed validation or broke a business rule.",
}


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Describe error responses for OpenAPI using the shared error envelope."""
    return {
        code: {"model": ErrorResponse, "description": _ERROR_DESCRIPTIONS[code]}
        for code in status_codes
    }
