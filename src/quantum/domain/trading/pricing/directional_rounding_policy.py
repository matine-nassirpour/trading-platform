from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.trading.pricing.quantization_service import QuantizationService
from quantum.domain.trading.types.price_rounding import PriceRoundingMode
from quantum.domain.trading.value_objects.instrument_spec import InstrumentSpec


class DirectionalRoundingPolicy:
    """
    Canonical directional rounding policy for executable prices.

    Guarantees:
    - Broker-safe
    - Deterministic
    - Context-explicit
    """

    _ROUNDING_MAP = {
        PriceRoundingMode.FLOOR: ROUND_FLOOR,
        PriceRoundingMode.CEILING: ROUND_CEILING,
        PriceRoundingMode.NEAREST: ROUND_HALF_EVEN,
    }

    @staticmethod
    def quantize_price(
        *,
        value: Decimal,
        instrument: InstrumentSpec,
        mode: PriceRoundingMode,
    ) -> Decimal:
        """
        Quantizes a price using:
        1) multiple-of increment (market constraint)
        2) directional rounding (execution constraint)
        """

        if mode not in DirectionalRoundingPolicy._ROUNDING_MAP:
            raise InvariantViolation(f"Unsupported rounding mode: {mode}")

        # Step 1 — market increment
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=instrument.price_increment,
        )

        # Step 2 — directional rounding
        rounding = DirectionalRoundingPolicy._ROUNDING_MAP[mode]

        return raw.quantize(
            instrument.price_scale,
            rounding=rounding,
        )
