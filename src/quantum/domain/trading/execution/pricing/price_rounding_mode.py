from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class PriceRoundingMode(ClosedSetValueObject):
    """
    Canonical directional rounding mode for executable prices.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "floor",
                "ceiling",
                "nearest",
            }
        )

    def decimal_rounding(self) -> str:
        """
        Returns the corresponding Decimal rounding mode.
        """
        if self.value == "floor":
            return ROUND_FLOOR
        if self.value == "ceiling":
            return ROUND_CEILING
        if self.value == "nearest":
            return ROUND_HALF_EVEN

        # Defensive: should be unreachable due to closed-set invariant
        raise RuntimeError(f"Unsupported PriceRoundingMode: {self.value}")
