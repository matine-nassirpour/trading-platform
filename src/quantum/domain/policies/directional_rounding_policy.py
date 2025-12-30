from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.services.quantization_service import QuantizationService
from quantum.domain.types.price_rounding import PriceRoundingMode


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
