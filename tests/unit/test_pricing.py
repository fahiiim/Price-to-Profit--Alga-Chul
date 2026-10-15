from decimal import Decimal as D

import pytest

from app.pricing import (
    Deposit,
    DepositMode,
    HairLine,
    ItemLine,
    LabourLine,
    PricingError,
    calculate_deposit,
    price_line,
    price_quote,
)

WORKED_EXAMPLE_LINES = [
    HairLine(
        grams_required=D("170"),
        grams_per_pack=D("100"),
        pack_price=D("350"),
        markup_percent=D("60"),
    ),
    LabourLine(hours=D("3.5"), hourly_rate=D("180")),
    ItemLine(quantity=D("1"), unit_price=D("80"), unit_cost=D("40")),
    ItemLine(quantity=D("1"), unit_price=D("150")),
    ItemLine(quantity=D("1"), unit_price=D("25"), unit_cost=D("25"), taxable=False),
]


def test_worked_example_matches_the_spec() -> None:
    priced = price_quote(
        WORKED_EXAMPLE_LINES,
        tax_rate_percent=D("5"),
        deposit=Deposit(DepositMode.FIXED, D("600")),
    )
    totals = priced.totals

    assert [line.price for line in priced.lines] == [
        D("1120.00"),
        D("630.00"),
        D("80.00"),
        D("150.00"),
        D("25.00"),
    ]
    assert totals.subtotal == D("2005.00")
    assert totals.taxable_amount == D("1980.00")
    assert totals.tax_amount == D("99.00")
    assert totals.total == D("2104.00")
    assert totals.deposit_amount == D("600.00")
    assert totals.balance_due == D("1504.00")
    assert totals.total_cost == D("765.00")
    assert totals.profit == D("1240.00")
    assert totals.labour_hours == D("3.5")
    assert totals.profit_per_hour == D("354.29")
    assert totals.margin_percent == D("61.85")


def test_hair_in_whole_packs_reports_packs_and_leftover() -> None:
    result = price_line(WORKED_EXAMPLE_LINES[0])

    assert result.cost_per_gram == D("3.5000")
    assert result.packs_needed == 2
    assert result.leftover_grams == D("30.00")
    assert result.cost == D("700.00")
    assert result.price == D("1120.00")


def test_hair_by_the_gram_charges_only_what_is_used() -> None:
    line = HairLine(
        grams_required=D("170"),
        grams_per_pack=D("100"),
        pack_price=D("350"),
        markup_percent=D("60"),
        whole_packs=False,
    )
    result = price_line(line)

    assert result.cost == D("595.00")
    assert result.price == D("952.00")
    assert result.leftover_grams == D("0.00")


def test_exact_pack_multiple_has_no_leftover() -> None:
    line = HairLine(
        grams_required=D("200"),
        grams_per_pack=D("100"),
        pack_price=D("350"),
        markup_percent=D("0"),
    )
    result = price_line(line)

    assert result.packs_needed == 2
    assert result.leftover_grams == D("0.00")


def test_rounding_is_half_up_to_cents() -> None:
    result = price_line(ItemLine(quantity=D("3"), unit_price=D("0.335")))
    assert result.price == D("1.01")


def test_percentage_deposit_and_cap_at_total() -> None:
    assert calculate_deposit(D("2104"), Deposit(DepositMode.PERCENT, D("30"))) == D(
        "631.20"
    )
    assert calculate_deposit(D("100"), Deposit(DepositMode.FIXED, D("500"))) == D("100")
    assert calculate_deposit(D("100"), None) == D("0")


def test_no_labour_means_no_profit_per_hour() -> None:
    priced = price_quote(
        [ItemLine(quantity=D("1"), unit_price=D("100"), unit_cost=D("30"))],
        tax_rate_percent=D("0"),
    )
    assert priced.totals.profit == D("70.00")
    assert priced.totals.profit_per_hour is None


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (
            HairLine(
                grams_required=D("10"),
                grams_per_pack=D("0"),
                pack_price=D("1"),
                markup_percent=D("0"),
            ),
            "grams_per_pack",
        ),
        (LabourLine(hours=D("0"), hourly_rate=D("100")), "hours"),
        (ItemLine(quantity=D("1"), unit_price=D("-1")), "unit_price"),
    ],
)
def test_invalid_inputs_raise_pricing_error(line, message: str) -> None:
    with pytest.raises(PricingError, match=message):
        price_line(line)


def test_tax_rate_above_100_is_rejected() -> None:
    with pytest.raises(PricingError, match="tax_rate_percent"):
        price_quote(WORKED_EXAMPLE_LINES, tax_rate_percent=D("101"))
