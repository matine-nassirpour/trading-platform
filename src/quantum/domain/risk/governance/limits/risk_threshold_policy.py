from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskThresholdPolicy(ClosedSetValueObject):
    """
    Defines how risk thresholds are evaluated.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "inclusive",  # breach at >= limit
                "exclusive",  # breach at > limit
            }
        )

    def is_breached(self, value: Decimal, limit: Decimal) -> bool:
        if self.value == "inclusive":
            return value >= limit
        if self.value == "exclusive":
            return value > limit
        raise InvariantViolation(f"Unknown policy: {self.value}")

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def inclusive(cls) -> RiskThresholdPolicy:
        return cls("inclusive")

    @classmethod
    def exclusive(cls) -> RiskThresholdPolicy:
        return cls("exclusive")
