from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.trading.pricing.quantization_service import QuantizationService
from quantum.domain.trading.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.trading.value_objects.position_side import PositionSide
from quantum.domain.trading.value_objects.pricing_context import PricingContext


class PricingPolicy:
    """
    Canonical and SINGLE pricing policy for the entire Domain.

    Responsibilities:
    - Apply market increment constraints
    - Apply decimal scale constraints
    - Apply context-aware rounding rules
    - Remain deterministic and auditable

    This class is the ONLY allowed entry point
    for price / volume quantization in the Domain.
    """

    _NEUTRAL_ROUNDING: Final[str] = ROUND_HALF_EVEN

    # --- Internal decision logic ---------------------------------------------

    @staticmethod
    def _execution_rounding(
        *,
        context: PricingContext,
        side: PositionSide,
    ) -> str:
        """
        Determines execution-safe rounding based on context and position side.
        """

        if context.is_execution_sl():
            return ROUND_FLOOR if side.is_long() else ROUND_CEILING

        if context.is_execution_tp():
            return ROUND_CEILING if side.is_long() else ROUND_FLOOR

        raise InvariantViolation(f"Unsupported execution pricing context: {context}")

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

        Rules:
        1) Multiple-of increment (market constraint)
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
            rounding = PricingPolicy._execution_rounding(
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
