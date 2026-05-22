import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_SYMBOL_RE = re.compile(r"^[A-Z0-9._\-]{3,20}$")


@dataclass(frozen=True, slots=True)
class Symbol(ValueObject):
    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("Symbol must be a string")

        canonical = self.value.strip().upper()

        if not canonical:
            raise InvariantViolation("Symbol must not be empty")

        if self.value != canonical:
            raise InvariantViolation(
                f"Symbol must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if _SYMBOL_RE.fullmatch(self.value) is None:
            raise InvariantViolation(f"Invalid symbol: {self.value!r}")

    def __str__(self) -> str:
        return self.value
