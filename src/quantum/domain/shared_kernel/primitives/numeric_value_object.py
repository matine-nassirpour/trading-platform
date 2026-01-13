from __future__ import annotations

from abc import ABC
from decimal import Decimal

from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@immutable_dataclass
class NumericValueObject(ValueObject, ABC):
    """
    Canonical base class for all numeric Value Objects.

    HARD GUARANTEES:
    - Decimal only
    - No NaN
    - No Infinity
    - These guarantees are NON-OVERRIDABLE
    """

    value: Decimal

    # --- Base numeric invariants ----------------------------------------------

    def _validate_base(self, key: MutationKey) -> None:
        """
        Injected into the FINAL validation pipeline.

        This cannot be bypassed or reordered.
        """

        if not isinstance(self.value, Decimal):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a Decimal"
            )

        if self.value.is_nan():
            raise InvariantViolation(f"{self.__class__.__name__} must not be NaN")

        if self.value.is_infinite():
            raise InvariantViolation(f"{self.__class__.__name__} must be finite")

    # --- Guard against override -----------------------------------------------

    def __init_subclass__(cls) -> None:
        forbidden = {"_validate_base"}

        for name in forbidden:
            if name in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__} is not allowed to override {name} "
                    "(numeric safety is non-negotiable)"
                )

        super().__init_subclass__()
