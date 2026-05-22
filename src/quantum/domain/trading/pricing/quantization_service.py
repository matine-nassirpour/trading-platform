from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class QuantizationService(DomainService):
    """
    Canonical multiple-of-increment quantization.

    Guarantees:
    - Deterministic
    - Broker-aligned
    - Multiple-of-increment
    - Rounding mode applied at increment level
    """

    __slots__ = ()

    DEFAULT_ROUNDING_MODE: Final[str] = ROUND_HALF_EVEN

    @staticmethod
    def quantize_to_increment(
        *,
        value: Decimal,
        increment: Decimal,
        rounding: str = DEFAULT_ROUNDING_MODE,
    ) -> Decimal:
        """
        Quantize `value` to the nearest multiple of `increment`.

        Example:
            value=1.13, increment=0.25 → 1.25
            value=1.12, increment=0.25 → 1.00
        """
        if increment <= Decimal("0"):
            raise InvariantViolation("increment must be strictly positive")

        if value.is_nan() or value.is_infinite():
            raise InvariantViolation("value must be finite")

        if increment.is_nan() or increment.is_infinite():
            raise InvariantViolation("increment must be finite")

        multiplier = (value / increment).to_integral_value(rounding=rounding)

        return multiplier * increment
