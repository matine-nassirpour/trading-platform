from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class ExecutionRejection(ValueObject):
    code: str
    description: str

    def _validate(self) -> None:
        if not self.code:
            raise InvariantViolation("Rejection code must not be empty")

        if not isinstance(self.description, str) or not self.description.strip():
            raise InvariantViolation("Rejection description must not be empty")
