"""Vocabulary shared by pricing, the library and quotes."""

from enum import StrEnum


class LineKind(StrEnum):
    """What a quote line (or a saved library item) represents."""

    HAIR = "hair"
    """Hair sold by weight and bought in packs. Markup applies."""

    LABOUR = "labour"
    """Time charged by the hour, such as installation."""

    SERVICE = "service"
    """A fixed-price service, such as toning or a consultation."""

    MATERIAL = "material"
    """Products used during the appointment, such as tapes or bonds."""

    FEE = "fee"
    """Any other charge, such as shipping or a call-out fee."""


class DepositMode(StrEnum):
    """How the deposit is expressed."""

    PERCENT = "percent"
    """A percentage of the quote total."""

    FIXED = "fixed"
    """A fixed amount of money."""
