import uuid

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class ExecutionId(ValueObject):
    """
    Canonical unique execution identifier.
    """

    value: uuid.UUID

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("ExecutionId must be a UUID")
