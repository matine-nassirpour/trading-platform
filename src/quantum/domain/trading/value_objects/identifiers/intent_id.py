import uuid

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class IntentId(ValueObject):
    value: uuid.UUID

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("IntentId must be a UUID")
