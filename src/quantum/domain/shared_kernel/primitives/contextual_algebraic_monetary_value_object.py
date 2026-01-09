from __future__ import annotations

from abc import ABC

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.primitives.algebraic_monetary_value_object import (
    AlgebraicMonetaryValueObject,
)


class ContextualAlgebraicMonetaryValueObject(
    AlgebraicMonetaryValueObject,
    ContextualMonetaryAmount,
    ABC,
):
    """
    Algebraic monetary value bound to a MoneyContext.

    Guarantees:
    - Currency consistency
    - Context consistency
    - Safe algebraic operations
    """

    def _check_context(self, other: ContextualAlgebraicMonetaryValueObject) -> None:
        if self.context != other.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {self.context} vs {other.context}"
            )
