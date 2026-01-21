from __future__ import annotations

import uuid

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CorrelationId(ValueObject):
    """
    Correlates multiple events belonging to the same logical flow.

    Example:
        - One trading decision
        - One execution chain
        - One risk evaluation
    """

    value: uuid.UUID

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("CorrelationId must be a UUID")

    @staticmethod
    def new() -> CorrelationId:
        return CorrelationId(uuid.uuid4())

    def __str__(self) -> str:
        return str(self.value)
