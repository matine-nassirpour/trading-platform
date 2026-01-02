from decimal import Decimal
from typing import Final

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.trading.pricing.quantization_service import QuantizationService
from quantum.domain.trading.pricing.rounding_strategy import _RoundingStrategy
from quantum.domain.trading.value_objects.instrument.instrument_spec import (
    InstrumentSpec,
)
from quantum.domain.trading.value_objects.order.position_side import PositionSide
from quantum.domain.trading.value_objects.pricing.pricing_context import PricingContext


class PricingPolicy:
    """
    Canonical and SINGLE pricing policy for the entire Domain.

    Rules:
    - This is the ONLY allowed pricing entry point.
    - All executable pricing MUST go through this policy.
    - No alternative pricing services are allowed.
    """

    _NEUTRAL_ROUNDING: Final[str] = _RoundingStrategy.NEUTRAL

    # --- Price ----------------------------------------------------------------

    @staticmethod
    def quantize_price(
        *,
        value: Decimal,
        instrument: InstrumentSpec,
        context: PricingContext,
        side: PositionSide | None = None,
    ) -> Decimal:
        """
        Canonical price quantization.

        Pipeline:
        1) Market increment (multiple-of-increment)
        2) Context-aware directional rounding
        3) Decimal scale quantization
        """

        if not isinstance(context, PricingContext):
            raise InvariantViolation("Invalid PricingContext")

        if not context.is_neutral() and side is None:
            raise InvariantViolation(
                "Execution pricing requires an explicit PositionSide"
            )

        # Step 1 — market increment
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=instrument.price_increment,
        )

        # Step 2 — rounding selection
        if context.is_neutral():
            rounding = PricingPolicy._NEUTRAL_ROUNDING
        else:
            if not isinstance(side, PositionSide):
                raise InvariantViolation("Invalid PositionSide")

            rounding = _RoundingStrategy.execution(
                context=context,
                side=side,
            )

        # Step 3 — decimal scale
        return raw.quantize(
            instrument.price_scale,
            rounding=rounding,
        )

    # --- Volume ---------------------------------------------------------------

    @staticmethod
    def quantize_volume(
        *,
        value: Decimal,
        instrument: InstrumentSpec,
    ) -> Decimal:
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=instrument.volume_increment,
        )

        return raw.quantize(
            instrument.volume_scale,
            rounding=PricingPolicy._NEUTRAL_ROUNDING,
        )

    # --- Money ----------------------------------------------------------------

    @staticmethod
    def quantize_money(
        *,
        value: Decimal,
        instrument: InstrumentSpec,
    ) -> Decimal:
        return value.quantize(
            instrument.money_scale,
            rounding=PricingPolicy._NEUTRAL_ROUNDING,
        )

    # --- Comparisons (price) --------------------------------------------------

    @staticmethod
    def price_equal(
        a: Decimal,
        b: Decimal,
        instrument: InstrumentSpec,
    ) -> bool:
        qa = PricingPolicy.quantize_price(
            value=a,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        qb = PricingPolicy.quantize_price(
            value=b,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        return qa == qb

    @staticmethod
    def price_less_than(
        a: Decimal,
        b: Decimal,
        instrument: InstrumentSpec,
    ) -> bool:
        qa = PricingPolicy.quantize_price(
            value=a,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        qb = PricingPolicy.quantize_price(
            value=b,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        return qa < qb

    @staticmethod
    def price_greater_than(
        a: Decimal,
        b: Decimal,
        instrument: InstrumentSpec,
    ) -> bool:
        qa = PricingPolicy.quantize_price(
            value=a,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        qb = PricingPolicy.quantize_price(
            value=b,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        return qa > qb
