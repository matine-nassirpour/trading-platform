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

    HARD GUARANTEES:
    - Decimal-only
    - No NaN
    - No Infinity
    - Fundamental numeric invariants are NON-OVERRIDABLE

    Architectural contract:
    - Subclasses MAY define semantic constraints
    - Subclasses MUST NOT alter numeric safety guarantees
    """

    value: Decimal

    # --- Validation entrypoint ------------------------------------------------

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """
        FINAL validation entrypoint.

        Order is STRICT and MUST NOT be altered:
        1. numeric fundamentals
        2. semantic constraints
        """
        self.__validate_numeric_fundamentals()
        self._validate_semantics()

    # --- Fundamental invariants (NON-OVERRIDABLE) -----------------------------

    def __validate_numeric_fundamentals(self) -> None:
        """
        Enforces all fundamental numeric invariants.

        This method is:
        - private (name-mangled)
        - unreachable for override
        - enforced for all subclasses
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
        """
        raise NotImplementedError

    # --- Subclass override guard (HARD FAIL) ----------------------------------

    def __init_subclass__(cls) -> None:
        """
        Prevents subclasses from redefining numeric fundamental validation.

        This is a HARD architectural guard.
        """

        forbidden = {
            "_validate",
            "_NumericValueObject__validate_numeric_fundamentals",
            "_validate_numeric_fundamentals",
            "__post_init__",
        }

        for name in forbidden:
            if name in cls.__dict__:
                raise TypeError(f"{cls.__name__} is not allowed to override {name}")

        super().__init_subclass__()
