from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.trading.pricing.quantization_service import QuantizationService
from quantum.domain.trading.value_objects.instrument.instrument_spec import (
    InstrumentSpec,
)
from quantum.domain.trading.value_objects.pricing.price_rounding_mode import (
    PriceRoundingMode,
)


class DirectionalRoundingPolicy:
    """
    Canonical directional rounding policy for executable prices.

    Guarantees:
    - Broker-safe
    - Deterministic
    - Context-explicit
    """

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

        if not isinstance(mode, PriceRoundingMode):
            raise InvariantViolation("Invalid PriceRoundingMode")

        # Step 1 — market increment
        raw = QuantizationService.quantize_to_increment(
            value=value,
            increment=instrument.price_increment,
        )

        # Step 2 — directional rounding (delegated to VO)
        return raw.quantize(
            instrument.price_scale,
            rounding=mode.decimal_rounding(),
        )
