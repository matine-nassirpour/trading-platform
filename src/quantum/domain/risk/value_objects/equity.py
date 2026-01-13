from __future__ import annotations

from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.value_objects.currency import Currency
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


@immutable_dataclass
class Equity(ContextualMonetaryAmount):
    """
    Desk equity, bound to a MoneyContext.

    Algebra:
    - Equity ⊕ RealizedPnL → Equity
    - Equity ⊖ RealizedPnL → Equity

    Notes:
    - Equity may be negative (margin trading).
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _monetary_kind(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
        # Enforce MoneyContext ↔ currency consistency (via parent)
        super()._validate_semantics(key)
        # No further constraint: Equity ∈ ℝ

    def _assert_compatible_pnl(self, pnl: RealizedPnL) -> None:
        if not isinstance(pnl, RealizedPnL):
            raise InvariantViolation("Equity adjustment requires a RealizedPnL")

        if pnl.context != self.context:
            raise InvariantViolation("RealizedPnL MoneyContext mismatch")

        # Redundant with context check, but makes the invariant explicit and local
        if pnl.currency != self.currency:
            raise InvariantViolation("RealizedPnL currency mismatch")

    def add(self, pnl: RealizedPnL) -> Equity:
        """
        Returns a new Equity adjusted upward by the given realized PnL.
        """
        self._assert_compatible_pnl(pnl)

        return Equity(
            value=self.value + pnl.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, pnl: RealizedPnL) -> Equity:
        """
        Returns a new Equity adjusted downward by the given realized PnL.

        Semantic note:
        - subtracting a negative pnl increases equity, which is mathematically consistent.
        """
        self._assert_compatible_pnl(pnl)

        return Equity(
            value=self.value - pnl.value,
            currency=self.currency,
            context=self.context,
        )
