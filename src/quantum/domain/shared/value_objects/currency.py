from __future__ import annotations

from dataclasses import dataclass
from re import fullmatch

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject

_ISO_4217_RE = fullmatch


@dataclass(frozen=True)
class Currency(ValueObject):
    """
    ISO 4217 currency code.

    Examples: USD, EUR, JPY, CHF
    """

    code: str

    def _validate(self) -> None:
        if not isinstance(self.code, str):
            raise InvariantViolation("Currency code must be a string")

        value = self.code.strip().upper()

        if not _ISO_4217_RE(r"[A-Z]{3}", value):
            raise InvariantViolation(f"Invalid ISO 4217 currency code: {self.code}")

        object.__setattr__(self, "code", value)

    def __str__(self) -> str:
        return self.code
