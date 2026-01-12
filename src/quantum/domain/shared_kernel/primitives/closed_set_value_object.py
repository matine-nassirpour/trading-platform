from __future__ import annotations

from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


def _canonicalize(value: str) -> str:
    """
    Canonical normalization function for closed-set values.

    This function defines the ONLY valid representation
    of any closed-set value in the entire system.
    """
    return value.strip().lower()


def _validate_allowed_values(values: Iterable[str], cls_name: str) -> frozenset[str]:
    """
    Enforces that _ALLOWED_VALUES is already canonical and valid.

    This runs at CLASS DEFINITION TIME, not at runtime.
    """
    if not isinstance(values, (set, frozenset)):
        raise TypeError(
            f"{cls_name}._ALLOWED_VALUES must be a set or frozenset of strings"
        )

    canonical = set()

    for v in values:
        if not isinstance(v, str):
            raise TypeError(
                f"{cls_name}._ALLOWED_VALUES must contain only strings, got {type(v)}"
            )

        c = _canonicalize(v)

        if c != v:
            raise TypeError(
                f"{cls_name}._ALLOWED_VALUES must contain ONLY canonical values. "
                f"Invalid entry: {v!r} (expected {c!r})"
            )

        canonical.add(c)

    if not canonical:
        raise TypeError(f"{cls_name}._ALLOWED_VALUES must not be empty")

    return frozenset(canonical)


@dataclass(slots=True)
class ClosedSetValueObject(ValueObject, ABC):
    """
    Canonical base class for closed-set domain concepts.

    HARD GUARANTEES:
    - Domain values are finite and explicitly enumerated
    - Canonical representation is globally enforced
    - Validation is deterministic and idempotent
    - Contracts (JSON, FIX, APIs) see only canonical values
    """

    value: str

    # MUST be overridden by subclasses
    _ALLOWED_VALUES: ClassVar[frozenset[str]]

    # --- Subclass contract enforcement ----------------------------------------

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "_ALLOWED_VALUES"):
            raise TypeError(
                f"{cls.__name__} must define _ALLOWED_VALUES as a frozenset[str]"
            )

        cls._ALLOWED_VALUES = _validate_allowed_values(
            cls._ALLOWED_VALUES, cls.__name__
        )

        super().__init_subclass__()

    # --- Semantic invariants --------------------------------------------------

    def _validate_semantics(self, key: Any) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a string"
            )

        canonical = _canonicalize(self.value)

        if canonical not in self._ALLOWED_VALUES:
            raise InvariantViolation(
                f"{self.__class__.__name__} invalid value: {self.value!r}. "
                f"Allowed values: {sorted(self._ALLOWED_VALUES)}"
            )

        # Store canonical representation
        object.__setattr__(self, "value", canonical)

    # --- Canonical string form ------------------------------------------------

    def __str__(self) -> str:
        return self.value
