from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


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
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    @classmethod
    def inclusive(cls) -> RiskThresholdPolicy:
        return cls("inclusive")

    @classmethod
    def exclusive(cls) -> RiskThresholdPolicy:
        return cls("exclusive")
