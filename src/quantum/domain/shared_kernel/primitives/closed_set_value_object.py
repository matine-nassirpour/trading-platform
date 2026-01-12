from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class ClosedSetValueObject(ValueObject, ABC):
    """
    Canonical base class for closed-set domain concepts.

    Guarantees:
    - Finite, explicitly enumerated domain values
    - Strong typing (not a language enum)
    - Deterministic validation
    - Contract-friendly string representation
    """

    value: str

    # MUST be overridden by subclasses
    _ALLOWED_VALUES: ClassVar[frozenset[str]]

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a string"
            )

        normalized = self.value.strip().lower()

        if normalized not in self._ALLOWED_VALUES:
            raise InvariantViolation(
                f"{self.__class__.__name__} invalid value: {self.value!r}"
            )

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
