from __future__ import annotations

from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.contextual_algebraic_monetary_value_object import (
    ContextualAlgebraicMonetaryValueObject,
)
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.value_objects.currency import Currency


@immutable_dataclass
class UnrealizedPnL(ContextualAlgebraicMonetaryValueObject):
    """
    Unrealized PnL bound to a MoneyContext.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _monetary_kind(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self, key: MutationKey) -> None:
        """
        PnL ∈ ℝ, but:
        - must be a valid Decimal
        - must belong to a valid Currency
        - must belong to a valid MoneyContext
        """
        super()._validate_semantics(key)
        # No further restriction on sign

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: UnrealizedPnL) -> UnrealizedPnL:
        self._assert_algebraically_compatible(other)
        return UnrealizedPnL(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: UnrealizedPnL) -> UnrealizedPnL:
        self._assert_algebraically_compatible(other)
        return UnrealizedPnL(
            value=self.value - other.value,
            currency=self.currency,
            context=self.context,
        )

    @staticmethod
    def zero(context: MoneyContext) -> UnrealizedPnL:
        return UnrealizedPnL(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )
