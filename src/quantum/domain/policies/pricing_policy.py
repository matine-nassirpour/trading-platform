from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.services.quantization_service import QuantizationService
from quantum.domain.types.position_side import PositionSide
from quantum.domain.types.pricing_context import PricingContext


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

    _ROUNDING_MATRIX: Final[dict[tuple[PricingContext, PositionSide], str]] = {
        # --- Neutral (non-executable)
        (PricingContext.NEUTRAL, PositionSide.LONG): ROUND_HALF_EVEN,
        (PricingContext.NEUTRAL, PositionSide.SHORT): ROUND_HALF_EVEN,
        # --- Stop Loss (worst-case)
        (PricingContext.EXECUTION_SL, PositionSide.LONG): ROUND_FLOOR,
        (PricingContext.EXECUTION_SL, PositionSide.SHORT): ROUND_CEILING,
        # --- Take Profit (best-case)
        (PricingContext.EXECUTION_TP, PositionSide.LONG): ROUND_CEILING,
        (PricingContext.EXECUTION_TP, PositionSide.SHORT): ROUND_FLOOR,
    }

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
        2) Decimal scale quantization (representation)
        3) Context-aware directional rounding (execution safety)
        """

        if context != PricingContext.NEUTRAL and side is None:
            raise InvariantViolation(
                "Execution pricing requires an explicit PositionSide"
            )

        # Step 1 — market increment
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=instrument.price_increment,
        )

        # Step 2 — rounding selection
        if context == PricingContext.NEUTRAL:
            rounding = PricingPolicy._NEUTRAL_ROUNDING
        else:
            try:
                rounding = PricingPolicy._ROUNDING_MATRIX[(context, side)]
            except KeyError:
                raise InvariantViolation(
                    f"Unsupported pricing context/side combination: {context}, {side}"
                ) from None

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
            context=PricingContext.NEUTRAL,
        )
        qb = PricingPolicy.quantize_price(
            value=b,
            instrument=instrument,
            context=PricingContext.NEUTRAL,
        )
        return qa == qb

    @staticmethod
    def price_less_than(
        a: Decimal,
        b: Decimal,
        instrument: InstrumentSpec,
    ) -> bool:
        return PricingPolicy.price_equal(a, b, instrument) is False and (
            PricingPolicy.quantize_price(
                value=a,
                instrument=instrument,
                context=PricingContext.NEUTRAL,
            )
            < PricingPolicy.quantize_price(
                value=b,
                instrument=instrument,
                context=PricingContext.NEUTRAL,
            )
        )

    @staticmethod
    def price_greater_than(
        a: Decimal,
        b: Decimal,
        instrument: InstrumentSpec,
    ) -> bool:
        return PricingPolicy.price_equal(a, b, instrument) is False and (
            PricingPolicy.quantize_price(
                value=a,
                instrument=instrument,
                context=PricingContext.NEUTRAL,
            )
            > PricingPolicy.quantize_price(
                value=b,
                instrument=instrument,
                context=PricingContext.NEUTRAL,
            )
        )
