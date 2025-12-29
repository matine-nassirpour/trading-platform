from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec


class PricingPolicy:
    """
    Canonical pricing and quantization rules.

    Stateless.
    Deterministic.
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

    # --- Equality & ordering (canonical) --------------------------------------

    @staticmethod
    def price_equal(a: Decimal, b: Decimal, spec: InstrumentSpec) -> bool:
        """
        Equality after quantization (canonical definition).
        """
        return PricingPolicy.quantize_price(a, spec) == PricingPolicy.quantize_price(
            b, spec
        )

    @staticmethod
    def price_less_than(a: Decimal, b: Decimal, spec: InstrumentSpec) -> bool:
        return PricingPolicy.quantize_price(a, spec) < PricingPolicy.quantize_price(
            b, spec
        )

    @staticmethod
    def price_greater_than(a: Decimal, b: Decimal, spec: InstrumentSpec) -> bool:
        return PricingPolicy.quantize_price(a, spec) > PricingPolicy.quantize_price(
            b, spec
        )
