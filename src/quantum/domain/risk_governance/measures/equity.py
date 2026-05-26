from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class Equity(ContextualMonetaryAmount):
    """
    Desk equity, bound to a MoneyContext.

    Algebra:
    - Equity ⊕ RealizedPnL → Equity
    - Equity ⊖ RealizedPnL → Equity

    Notes:
    - Equity may be negative (margin trading).
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "equity"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()
        # Equity ∈ ℝ → no sign restriction

    # --- Algebra --------------------------------------------------------------

    def _assert_compatible_pnl(self, pnl: RealizedPnL) -> None:
        if not isinstance(pnl, RealizedPnL):
            raise InvariantViolation("Equity adjustment requires a RealizedPnL")

        if pnl.context != self.context:
            raise InvariantViolation("RealizedPnL MoneyContext mismatch")

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
        """
        self._assert_compatible_pnl(pnl)

        return Equity(
            value=self.value - pnl.value,
            currency=self.currency,
            context=self.context,
        )
