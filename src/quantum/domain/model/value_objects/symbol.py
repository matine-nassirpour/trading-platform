import re

from dataclasses import dataclass

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject

_SYMBOL_RE = re.compile(r"^[A-Z0-9._\-]{3,20}$")


@dataclass(frozen=True)
class Symbol(ValueObject):
    value: str

    def _validate(self) -> None:
        v = self.value.strip().upper()
        if not _SYMBOL_RE.match(v):
            raise InvariantViolation(f"Invalid symbol: {self.value}")
        object.__setattr__(self, "value", v)
