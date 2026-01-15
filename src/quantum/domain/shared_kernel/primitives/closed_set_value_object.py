from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


def _canonicalize(value: str) -> str:
    """
    Canonical normalization function for closed-set values.
    """
    return value.strip().lower()


def _validate_allowed_values(values: frozenset[str], cls_name: str) -> frozenset[str]:
    """
    Validates that a closed set is:
    - A frozenset[str]
    - Non-empty
    - Fully canonicalized
    - Free of duplicates under canonicalization
    """

    if not isinstance(values, frozenset):
        raise TypeError(f"{cls_name}._allowed_values() must return a frozenset[str]")

    if not values:
        raise TypeError(f"{cls_name}._allowed_values() must not be empty")

    canonical: set[str] = set()

    for v in values:
        if not isinstance(v, str):
            raise TypeError(
                f"{cls_name}._allowed_values() must contain only strings, got {type(v)}"
            )

        c = _canonicalize(v)

        if v != c:
            raise TypeError(
                f"{cls_name}._allowed_values() must contain only canonical values. "
                f"Invalid entry: {v!r}, expected: {c!r}"
            )

        canonical.add(c)

    return frozenset(canonical)


@dataclass(frozen=True, slots=True)
class ClosedSetValueObject(ValueObject, ABC):
    """
    Algebraic closed-set Value Object.

    This represents a FINITE, EXPLICITLY ENUMERATED domain concept.

    HARD GUARANTEES:
    - The value space is finite and closed
    - All values are canonicalized
    - No subclass may exist without declaring its full domain
    - Invalid or partial implementations are rejected at import-time
    """

    value: str

    __ALLOWED_VALUES__: ClassVar[frozenset[str]]

    # --- Abstract contract ----------------------------------------------------

    @classmethod
    @abstractmethod
    def _allowed_values(cls) -> frozenset[str]:
        """
        Must return the complete, canonical finite set of allowed values.

        This is a TYPE-LEVEL contract, not a data attribute.
        """
        raise NotImplementedError

    # --- Import-time enforcement ----------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Abstract subclasses are allowed to omit the contract
        if cls is ClosedSetValueObject or cls.__abstractmethods__:
            return

        # Enforce explicit declaration of the closed set
        if "_allowed_values" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must explicitly implement _allowed_values()"
            )

        # Validate and freeze the closed set at import time
        values = cls._allowed_values()
        cls.__ALLOWED_VALUES__ = _validate_allowed_values(values, cls.__name__)

    # --- Semantic invariants --------------------------------------------------

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a string"
            )

        canonical = _canonicalize(self.value)

        if canonical not in self.__class__.__ALLOWED_VALUES__:
            raise InvariantViolation(
                f"{self.__class__.__name__} invalid value: {self.value!r}. "
                f"Allowed values: {sorted(self.__class__.__ALLOWED_VALUES__)}"
            )

        # Enforce canonical form
        object.__setattr__(self, "value", canonical)

    # --- Canonical string form ------------------------------------------------

    def __str__(self) -> str:
        return self.value
