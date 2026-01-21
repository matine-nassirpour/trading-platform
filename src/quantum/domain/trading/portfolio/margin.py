from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class Margin:
    """
    Represents margin usage and availability.
    """

    used: Decimal
    available: Decimal

    def _validate(self) -> None:
        if self.used < Decimal("0"):
            raise InvariantViolation("Used margin must be non-negative")

        if self.available < Decimal("0"):
            raise InvariantViolation("Available margin must be non-negative")

    def utilization_ratio(self) -> Decimal:
        total = self.used + self.available
        return Decimal("0") if total == 0 else self.used / total
