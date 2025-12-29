from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec


class PricingPolicy:
    """
    Canonical pricing and quantization rules.

    Stateless.
    """

    ROUNDING_MODE: Final[str] = ROUND_HALF_EVEN

    # --- Quantization ---------------------------------------------------------

    @staticmethod
    def quantize_price(value: Decimal, spec: InstrumentSpec) -> Decimal:
        return value.quantize(spec.price_tick, rounding=PricingPolicy.ROUNDING_MODE)

    @staticmethod
    def quantize_volume(value: Decimal, spec: InstrumentSpec) -> Decimal:
        return value.quantize(spec.volume_step, rounding=PricingPolicy.ROUNDING_MODE)

    @staticmethod
    def quantize_money(value: Decimal, spec: InstrumentSpec) -> Decimal:
        return value.quantize(spec.money_scale, rounding=PricingPolicy.ROUNDING_MODE)

    # --- Safe comparisons -----------------------------------------------------

    @staticmethod
    def price_equal(a: Decimal, b: Decimal, spec: InstrumentSpec) -> bool:
        return abs(a - b) <= spec.price_tick
