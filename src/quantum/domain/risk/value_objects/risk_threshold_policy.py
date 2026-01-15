from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


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

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def inclusive(cls) -> RiskThresholdPolicy:
        return cls("inclusive")

    @classmethod
    def exclusive(cls) -> RiskThresholdPolicy:
        return cls("exclusive")
