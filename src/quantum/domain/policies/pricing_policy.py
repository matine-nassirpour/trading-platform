from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.services.quantization_service import QuantizationService


class PricingPolicy:
    """
    Canonical pricing rules.

    ALL comparisons are done AFTER increment quantization.
    """

    ROUNDING_MODE: Final[str] = ROUND_HALF_EVEN

    # --- Price ----------------------------------------------------------------

    @staticmethod
    def quantize_price(value: Decimal, spec: InstrumentSpec) -> Decimal:
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=spec.price_increment,
        )
        return raw.quantize(spec.price_scale, rounding=PricingPolicy.ROUNDING_MODE)

    # --- Volume ---------------------------------------------------------------

    @staticmethod
    def quantize_volume(value: Decimal, spec: InstrumentSpec) -> Decimal:
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=spec.volume_increment,
        )
        return raw.quantize(spec.volume_increment, rounding=PricingPolicy.ROUNDING_MODE)

    # --- Money ----------------------------------------------------------------

    @staticmethod
    def quantize_money(value: Decimal, spec: InstrumentSpec) -> Decimal:
        return value.quantize(spec.money_scale, rounding=PricingPolicy.ROUNDING_MODE)

    # --- Comparisons ----------------------------------------------------------

    @staticmethod
    def price_equal(a: Decimal, b: Decimal, spec: InstrumentSpec) -> bool:
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
