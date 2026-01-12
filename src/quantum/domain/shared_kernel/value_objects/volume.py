from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True)
class PositiveVolume(NumericValueObject):
    """
    Volume strictly greater than zero.
    """

    value: Decimal

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: Any) -> None:
        if self.value <= Decimal("0"):
            raise InvariantViolation("PositiveVolume must be strictly > 0")


@dataclass(frozen=True)
class NonNegativeVolume(NumericValueObject):
    """
    Volume greater than or equal to zero.

    Use cases:
    - filled volume
    - partial fills
    - closed volume
    """

    value: Decimal

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: Any) -> None:
        if self.value < Decimal("0"):
            raise InvariantViolation("NonNegativeVolume must be ≥ 0")

    @classmethod
    def zero(cls) -> NonNegativeVolume:
        return cls(Decimal("0"))
