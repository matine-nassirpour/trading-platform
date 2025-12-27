from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final


class MonetaryPolicy:
    """
    Canonical monetary and precision policy for the domain.

    This policy defines:
    - allowed precision for prices and money
    - rounding strategy
    - comparison tolerances

    All financial computations in the domain MUST comply with this policy.
    """

    # --- Precision scales -----------------------------------------------------

    #: Minimal tick size for prices (e.g. FX, indices)
    PRICE_SCALE: Final[Decimal] = Decimal("0.00001")

    #: Minimal unit for money amounts (e.g. cents)
    MONEY_SCALE: Final[Decimal] = Decimal("0.01")

    #: Volume precision (lots, contracts, etc.)
    VOLUME_SCALE: Final[Decimal] = Decimal("0.01")

    # --- Rounding strategy ----------------------------------------------------

    ROUNDING_MODE: Final[str] = ROUND_HALF_EVEN

    # --- Comparison tolerances ------------------------------------------------

    PRICE_EPSILON: Final[Decimal] = PRICE_SCALE
    MONEY_EPSILON: Final[Decimal] = MONEY_SCALE
    VOLUME_EPSILON: Final[Decimal] = VOLUME_SCALE

    # --- Quantization helpers -------------------------------------------------

    @classmethod
    def quantize_price(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.PRICE_SCALE, rounding=cls.ROUNDING_MODE)

    @classmethod
    def quantize_money(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.MONEY_SCALE, rounding=cls.ROUNDING_MODE)

    @classmethod
    def quantize_volume(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.VOLUME_SCALE, rounding=cls.ROUNDING_MODE)

    # --- Safe comparisons -----------------------------------------------------

    @classmethod
    def price_equal(cls, a: Decimal, b: Decimal) -> bool:
        return abs(a - b) <= cls.PRICE_EPSILON

    @classmethod
    def money_equal(cls, a: Decimal, b: Decimal) -> bool:
        return abs(a - b) <= cls.MONEY_EPSILON

    @classmethod
    def volume_equal(cls, a: Decimal, b: Decimal) -> bool:
        return abs(a - b) <= cls.VOLUME_EPSILON
