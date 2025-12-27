from __future__ import annotations

import uuid

from dataclasses import dataclass

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class IntentId(ValueObject):
    value: uuid.UUID

    @classmethod
    def new(cls) -> IntentId:
        return cls(uuid.uuid4())

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("IntentId must be a UUID")


@dataclass(frozen=True)
class OrderId(ValueObject):
    value: int

    def _validate(self) -> None:
        if self.value < 1:
            raise InvariantViolation("OrderId must be ≥ 1")


@dataclass(frozen=True)
class DealId(ValueObject):
    value: int

    def _validate(self) -> None:
        if self.value < 1:
            raise InvariantViolation("DealId must be ≥ 1")


@dataclass(frozen=True)
class PositionId(ValueObject):
    value: int

    def _validate(self) -> None:
        if self.value < 1:
            raise InvariantViolation("PositionId must be ≥ 1")
