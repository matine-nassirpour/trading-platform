from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class PositionId(ValueObject):
    value: int

    def _validate(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvariantViolation("PositionId must be a strict int (not bool)")
        if self.value < 1:
            raise InvariantViolation("PositionId must be ≥ 1")
