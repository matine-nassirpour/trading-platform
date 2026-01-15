from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class RiskThresholdPolicy(ClosedSetValueObject):
    """
    Defines how risk thresholds are evaluated.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "inclusive",  # breach at >= limit
            "exclusive",  # breach at > limit
        }
    )

    @classmethod
    def inclusive(cls) -> RiskThresholdPolicy:
        return cls("inclusive")

    @classmethod
    def exclusive(cls) -> RiskThresholdPolicy:
        return cls("exclusive")
