from __future__ import annotations

import uuid

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


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

    def __str__(self) -> str:
        return str(self.value)
