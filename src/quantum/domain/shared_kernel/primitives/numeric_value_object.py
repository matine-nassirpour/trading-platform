from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class NumericValueObject(ValueObject, ABC):
    """
    Canonical base class for all numeric Value Objects.

    Design guarantees:
    - Immutable
    - Deterministic validation
    - Explicit numeric invariants
    - No NaN / Infinity
    - No floating-point arithmetic

    Architectural principles:
    - Fundamental numeric invariants are enforced ONCE here
    - Subclasses only define semantic constraints
    """

    value: Decimal

    # --- Validation entrypoint ------------------------------------------------

    def _validate(self) -> None:
        self._validate_numeric_fundamentals()
        self._validate_semantics()

    # --- Fundamental invariants (NON-OVERRIDABLE) -----------------------------

    def _validate_numeric_fundamentals(self) -> None:
        """
        Enforces all fundamental numeric invariants.

        This method MUST NOT be overridden.
        It defines the minimal safety contract for all numeric domain values.
        """
        if not isinstance(self.value, Decimal):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a Decimal"
            )

        if self.value.is_nan():
            raise InvariantViolation(f"{self.__class__.__name__} must not be NaN")

        if self.value.is_infinite():
            raise InvariantViolation(f"{self.__class__.__name__} must be finite")

    # --- Semantic invariants (OVERRIDABLE) ------------------------------------

    @abstractmethod
    def _validate_semantics(self) -> None:
        """
        Enforces domain-specific numeric invariants.

        Examples:
        - strictly positive
        - non-negative
        - bounded
        - sign-constrained
        """
        raise NotImplementedError
