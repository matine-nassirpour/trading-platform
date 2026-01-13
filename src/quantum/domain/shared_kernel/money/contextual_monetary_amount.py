from __future__ import annotations

from abc import ABC
from decimal import Decimal

from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.value_objects.currency import Currency


@immutable_dataclass
class ContextualMonetaryAmount(MonetaryAmount, ABC):
    """
    Monetary amount bound to a specific MoneyContext.

    This prevents cross-currency contamination at the system level.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _validate_semantics(self, key: MutationKey) -> None:
        """
        Validation pipeline:

        1. MonetaryAmount invariants (currency type, etc.)
        2. Context invariants
        3. Currency ∈ allowed_currencies
        """

        # --- Step 1: inherit and enforce ALL monetary invariants
        super()._validate_semantics(key)

        # --- Step 2: context must exist and be valid
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires a MoneyContext"
            )

        # --- Step 3: currency must be allowed by the context
        if self.currency not in self.context.allowed_currencies:
            raise InvariantViolation(
                f"Currency {self.currency} not allowed in MoneyContext {self.context}"
            )

    def _assert_same_context_and_currency(
        self, other: ContextualMonetaryAmount
    ) -> None:
        """
        Canonical invariant: both operands must belong to the same
        currency and the same MoneyContext.
        """

        if not isinstance(other, ContextualMonetaryAmount):
            raise InvariantViolation("Operand must be a ContextualMonetaryAmount")

        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

        if self.context != other.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {self.context} vs {other.context}"
            )
