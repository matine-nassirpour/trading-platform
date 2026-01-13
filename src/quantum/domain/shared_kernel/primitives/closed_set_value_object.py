from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar

from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


def _canonicalize(value: str) -> str:
    """
    Canonical normalization function for closed-set values.

    This function defines the ONLY valid representation
    of any closed-set value in the entire system.
    """
    return value.strip().lower()


def _validate_allowed_values(values: Iterable[str], cls_name: str) -> frozenset[str]:
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


@immutable_dataclass
class ClosedSetValueObject(ValueObject, ABC):
    """
    Canonical base class for closed-set domain concepts.

    HARD GUARANTEES:
    - Domain values are finite and explicitly enumerated
    - Canonical representation is globally enforced
    - Validation is deterministic and idempotent
    - This class is ABSTRACT and may never be instantiated
    """

    value: str

    _ALLOWED_VALUES: ClassVar[frozenset[str]]

    @abstractmethod
    def _closed_set_type(self) -> None:
        """
        Architectural tag.

        Forces ClosedSetValueObject to be abstract so it never violates
        DomainObject's 'no inherited role' rule.
        """
        raise NotImplementedError

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

    def _validate_semantics(self, key: MutationKey) -> None:
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

        self._mutate(key, "value", canonical)

    # --- Canonical string form ------------------------------------------------

    def __str__(self) -> str:
        return self.value
