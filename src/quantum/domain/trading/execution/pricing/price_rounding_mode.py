from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class PriceRoundingMode(ClosedSetValueObject):
    """
    Canonical directional rounding mode for executable prices.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "floor",
            "ceiling",
            "nearest",
        }
    )

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

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

        # Defensive: should be unreachable
        raise RuntimeError(f"Unsupported PriceRoundingMode: {self.value}")
