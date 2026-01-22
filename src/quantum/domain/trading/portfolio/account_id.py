from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class AccountId(ValueObject):
    value: str

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("AccountId must be a string")

        v = self.value.strip()
        if not v:
            raise InvariantViolation("AccountId must not be empty")

        object.__setattr__(self, "value", v)
