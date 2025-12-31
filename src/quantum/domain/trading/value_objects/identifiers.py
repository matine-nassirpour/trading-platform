from __future__ import annotations

import uuid

from dataclasses import dataclass

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject


def _validate_strict_positive_int(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvariantViolation(f"{name} must be a strict int (not bool)")
    if value < 1:
        raise InvariantViolation(f"{name} must be ≥ 1")


@dataclass(frozen=True)
class IntentId(ValueObject):
    value: uuid.UUID

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("IntentId must be a UUID")


@dataclass(frozen=True)
class OrderId(ValueObject):
    value: int

    def _validate(self) -> None:
        _validate_strict_positive_int(self.value, "OrderId")


@dataclass(frozen=True)
class PositionId(ValueObject):
    value: int

    def _validate(self) -> None:
        _validate_strict_positive_int(self.value, "PositionId")
