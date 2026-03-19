import inspect

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import final

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class NumericValueObject(ValueObject, ABC):
    """
    Canonical abstract base class for all numeric Value Objects.

    GUARANTEES:
    - Abstract by design: this class is NOT a complete domain concept
    - Decimal only
    - No NaN
    - No Infinity
    - Every concrete numeric type must explicitly declare its nominal identity

    ARCHITECTURAL CONSEQUENCE:
    NumericValueObject(value=...) is forbidden because it is semantically
    incomplete. Only concrete domain types may be instantiated.
    """

    value: Decimal

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is NumericValueObject:
            return

        if inspect.isabstract(cls):
            return

        if "nominal_type" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must explicitly implement nominal_type().")

    @classmethod
    @abstractmethod
    def nominal_type(cls) -> str:
        """
        Returns the canonical nominal domain identity of the concrete type.

        Examples:
            - 'realized_pnl'
            - 'unrealized_pnl'

        This is a TYPE-LEVEL semantic contract, not a display label.
        It exists to prevent semantically vague or anonymous numeric types.
        """
        raise NotImplementedError

    def _validate_numeric_value(self) -> None:
        """
        Final low-level numeric contract shared by all numeric value objects.
        """
        if not isinstance(self.value, Decimal):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a Decimal."
            )

        if self.value.is_nan():
            raise InvariantViolation(f"{self.__class__.__name__} must not be NaN.")

        if self.value.is_infinite():
            raise InvariantViolation(f"{self.__class__.__name__} must be finite.")

    def _validate_numeric_semantics(self) -> None:
        """
        Extension hook for subclasses.

        Override only when a subtype needs additional semantic constraints
        beyond the canonical Decimal contract.
        """
        return None

    @final
    def _validate_semantics(self) -> None:
        self._validate_numeric_value()
        self._validate_numeric_semantics()
