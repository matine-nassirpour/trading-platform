import uuid

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ExecutionId(ValueObject):
    """
    Canonical unique execution identifier.
    """

    value: uuid.UUID

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("ExecutionId must be a UUID")
