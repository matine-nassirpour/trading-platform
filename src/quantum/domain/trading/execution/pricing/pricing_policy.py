from decimal import Decimal
from typing import Final

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.execution.pricing.pricing_context import PricingContext
from quantum.domain.trading.execution.pricing.quantization_service import (
    QuantizationService,
)
from quantum.domain.trading.execution.pricing.rounding_strategy import _RoundingStrategy


class PricingPolicy(DomainService):
    """
    Canonical and SINGLE pricing policy for the entire Domain.

    Rules:
    - This is the ONLY allowed pricing entry point.
    - All executable pricing MUST go through this policy.
    - No alternative pricing services are allowed.
    - directional execution rounding is applied at increment level,
      not only at decimal-scale level.
    """

    __slots__ = ()

    _NEUTRAL_ROUNDING: Final[str] = _RoundingStrategy.NEUTRAL

    @staticmethod
    def _resolve_rounding(
        *,
        context: PricingContext,
        side: PositionSide | None,
    ) -> str:
        if context.is_neutral():
            return PricingPolicy._NEUTRAL_ROUNDING

        if not isinstance(side, PositionSide):
            raise InvariantViolation("Execution pricing requires a valid PositionSide")

        return _RoundingStrategy.execution(
            context=context,
            side=side,
        )

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
        """

        rounding = PricingPolicy._resolve_rounding(
            context=context,
            side=side,
        )

        increment_quantized = QuantizationService.quantize_to_increment(
            value=value,
            increment=instrument.price_increment,
            rounding=rounding,
        )

        return increment_quantized.quantize(
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
            rounding=PricingPolicy._NEUTRAL_ROUNDING,
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
