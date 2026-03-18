from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.money.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.money.money_context import MoneyContext


@dataclass(frozen=True, slots=True)
class ContextualMonetaryAmount(MonetaryAmount):
    """
    Monetary amount bound to a specific MoneyContext.

    HARD GUARANTEES:
    - Currency-aware
    - Context-aware
    - Immutable
    - No cross-context contamination
    - No cross-currency contamination
    """

    context: MoneyContext

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires a valid MoneyContext."
            )

        if self.currency not in self.context.allowed_currencies:
            raise InvariantViolation(
                f"{self.__class__.__name__}: currency {self.currency!s} "
                "is not allowed in MoneyContext."
            )

    # --- Algebraic compatibility contracts ------------------------------------

    def _assert_same_context_and_currency(
        self, other: ContextualMonetaryAmount
    ) -> None:
        """
        Ensures that two contextual monetary amounts are compatible
        at the monetary frame level.
        """
        if not isinstance(other, ContextualMonetaryAmount):
            raise InvariantViolation(
                f"Operand must be a ContextualMonetaryAmount, got {type(other).__name__}."
            )

        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency!s} vs {other.currency!s}."
            )

        if self.context != other.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {self.context!r} vs {other.context!r}."
            )

    def _assert_same_nominal_type(self, other: ContextualMonetaryAmount) -> None:
        """
        Enforces strict nominal typing at runtime.

        This is NON-NEGOTIABLE for domain safety:
        RealizedPnL != UnrealizedPnL even if they share the same structure.
        """
        if type(self) is not type(other):
            raise InvariantViolation(
                f"Nominal type mismatch: {type(self).__name__} vs {type(other).__name__}."
            )

    def _assert_closed_algebra_compatibility(
        self, other: ContextualMonetaryAmount
    ) -> None:
        """
        Full runtime compatibility check for closed algebraic operations.
        """
        self._assert_same_nominal_type(other)
        self._assert_same_context_and_currency(other)

    # --- Controlled reconstruction --------------------------------------------

    def _rebuild_with_value(self, value: Decimal) -> ContextualMonetaryAmount:
        """
        Reconstructs a new instance of the SAME concrete type.

        This method is intentionally centralized so algebraic subclasses
        can rely on one canonical reconstruction path.
        """
        return self.__class__(
            value=value,
            currency=self.currency,
            context=self.context,
        )
