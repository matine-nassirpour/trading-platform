from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.shared.errors.invariants import InvariantViolation


class QuantizationService:
    """
    Canonical multiple-of-increment quantization.

    Guarantees:
    - Deterministic
    - Broker-aligned
    - Multiple-of-increment (NOT decimal scale)
    """

    ROUNDING_MODE: Final[str] = ROUND_HALF_EVEN

    @staticmethod
    def quantize_to_increment(
        *,
        value: Decimal,
        increment: Decimal,
    ) -> Decimal:
        """
        Quantize `value` to the nearest multiple of `increment`.

        Example:
            value=1.13, increment=0.25 → 1.25
            value=1.12, increment=0.25 → 1.00
        """
        if increment <= Decimal("0"):
            raise InvariantViolation("Increment must be strictly positive")

        if value.is_nan() or value.is_infinite():
            raise InvariantViolation("Value must be finite")

        multiplier = (value / increment).to_integral_value(
            rounding=QuantizationService.ROUNDING_MODE
        )

        return multiplier * increment
