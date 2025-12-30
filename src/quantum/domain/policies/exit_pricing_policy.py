from decimal import Decimal

from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.policies.directional_rounding_policy import (
    DirectionalRoundingPolicy,
)
from quantum.domain.types.position_side import PositionSide
from quantum.domain.types.price_rounding import PriceRoundingMode


class ExitPricingPolicy:
    """
    Canonical executable rounding rules for SL / TP.

    Rules (industry standard):
    - SL → always toward worst case
    - TP → always toward best case
    """

    @staticmethod
    def rounding_for_sl(side: PositionSide) -> PriceRoundingMode:
        return (
            PriceRoundingMode.FLOOR
            if side == PositionSide.LONG
            else PriceRoundingMode.CEILING
        )

    @staticmethod
    def rounding_for_tp(side: PositionSide) -> PriceRoundingMode:
        return (
            PriceRoundingMode.CEILING
            if side == PositionSide.LONG
            else PriceRoundingMode.FLOOR
        )

    @staticmethod
    def quantize_sl(
        *,
        value: Decimal,
        side: PositionSide,
        instrument: InstrumentSpec,
    ) -> Decimal:
        return DirectionalRoundingPolicy.quantize_price(
            value=value,
            instrument=instrument,
            mode=ExitPricingPolicy.rounding_for_sl(side),
        )

    @staticmethod
    def quantize_tp(
        *,
        value: Decimal,
        side: PositionSide,
        instrument: InstrumentSpec,
    ) -> Decimal:
        return DirectionalRoundingPolicy.quantize_price(
            value=value,
            instrument=instrument,
            mode=ExitPricingPolicy.rounding_for_tp(side),
        )
