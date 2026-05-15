from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.foundation.contracts.violations import (
    StructuralContractViolation,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


def _canonicalize(value: str) -> str:
    """
    Canonical normalization function used only to validate canonical form.

    IMPORTANT:
    Domain objects do not normalize input.
    Normalization belongs to Anti-Corruption Layers.
    """
    return value.strip().lower()


def _is_canonical(value: str) -> bool:
    return value == _canonicalize(value)


def _validate_allowed_values(values: frozenset[str], cls_name: str) -> frozenset[str]:
    """
    Validates that a closed set is:
    - a frozenset[str]
    - non-empty
    - fully canonicalized
    """

    if not isinstance(values, frozenset):
        raise StructuralContractViolation(
            f"{cls_name}._allowed_values() must return a frozenset[str]."
        )

    if not values:
        raise StructuralContractViolation(
            f"{cls_name}._allowed_values() must not be empty."
        )

    canonical: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            raise StructuralContractViolation(
                f"{cls_name}._allowed_values() must contain only strings, "
                f"got {type(value).__name__}."
            )

        if not _is_canonical(value):
            raise StructuralContractViolation(
                f"{cls_name}._allowed_values() must contain only canonical values. "
                f"Invalid entry: {value!r}, expected: {_canonicalize(value)!r}."
            )

        canonical.add(value)

    return frozenset(canonical)


@dataclass(frozen=True, slots=True)
class ClosedSetValueObject(ValueObject, ABC):
    """
    Algebraic closed-set Value Object.

    IMPORTANT:
    This object does NOT normalize input values.
    Inputs must already be canonical.

    Normalization from external systems belongs to:
    - interfaces/
    - infrastructure/
    - Anti-Corruption Layers
    - mappers / translators / DTO parsers

    Domain consequence:
    - Currency("usd") is valid
    - Currency(" USD ") is rejected
    - Currency("USD") is rejected
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

        if cls is ClosedSetValueObject or cls.__abstractmethods__:
            return

        if "_allowed_values" not in cls.__dict__:
            raise StructuralContractViolation(
                f"{cls.__name__} must explicitly implement _allowed_values()."
            )

        cls.__ALLOWED_VALUES__ = _validate_allowed_values(
            cls._allowed_values(),
            cls.__name__,
        )

    # --- Semantic invariants --------------------------------------------------

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a string."
            )

        if not _is_canonical(self.value):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must already be canonical. "
                f"Got {self.value!r}, expected {_canonicalize(self.value)!r}. "
                "Normalization must happen outside the domain."
            )

        if self.value not in self.__class__.__ALLOWED_VALUES__:
            raise InvariantViolation(
                f"{self.__class__.__name__} invalid value: {self.value!r}. "
                f"Allowed values: {sorted(self.__class__.__ALLOWED_VALUES__)}."
            )

    # --- Canonical string form ------------------------------------------------

    def __str__(self) -> str:
        return self.value
