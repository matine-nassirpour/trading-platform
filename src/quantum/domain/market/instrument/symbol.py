import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation

_SYMBOL_RE = re.compile(r"^[A-Z0-9._\-]{3,20}$")


@dataclass(frozen=True, slots=True)
class Symbol(ValueObject):
    value: str

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("Symbol must be a string")

        v = self.value.strip().upper()

        if not _SYMBOL_RE.match(v):
            raise InvariantViolation(f"Invalid symbol: {self.value}")

        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
