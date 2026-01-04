from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.risk.events.v1.max_drawdown_exceeded_event import (
    MaxDrawdownExceededEvent,
)
from quantum.domain.risk.policies.risk_policy import RiskPolicy
from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.equity import Equity
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.aggregate_root import AggregateRoot
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


@dataclass(frozen=True)
class RiskState(AggregateRoot):
    """
    Aggregate Root encapsulating drawdown-based risk constraints.

    Canonical invariants:
    - equity_peak >= equity
    - drawdown = equity_peak - equity >= 0

    Architectural rule:
    - RiskState NEVER encodes threshold semantics directly.
    - Breach evaluation is delegated to RiskPolicy.
    """

    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        if self.equity.currency != self.equity_peak.currency:
            raise InvariantViolation("Currency mismatch in RiskState")

        if self.limits.max_drawdown.currency != self.equity.currency:
            raise InvariantViolation("Drawdown currency mismatch")

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("Equity peak cannot be below current equity")

    # --- Commands ------------------------------------------------------------

    def register_pnl(self, pnl: RealizedPnL, at: EpochMs) -> RiskState:
        """
        Applies a realized PnL to the equity and evaluates drawdown risk.

        Deterministic:
        - No side effects
        - No implicit policy
        - All breach semantics delegated to RiskPolicy
        """

        if pnl.currency != self.equity.currency:
            raise InvariantViolation("PnL currency mismatch")

        # 1. Update equity
        new_equity = self.equity.add(pnl)

        # 2. Update equity peak
        new_peak = (
            new_equity
            if new_equity.value > self.equity_peak.value
            else self.equity_peak
        )

        # 3. Compute drawdown (ALWAYS >= 0 by invariant)
        drawdown_value = new_peak.value - new_equity.value

        drawdown = Drawdown(
            value=drawdown_value,
            currency=new_equity.currency,
        )

        # 4. Produce new state (facts only)
        new_state = replace(
            self,
            equity=new_equity,
            equity_peak=new_peak,
        )

        # 5. Delegate breach evaluation to RiskPolicy
        breach = RiskPolicy.evaluate_drawdown(
            current_drawdown=drawdown,
            limits=self.limits,
        )

        if breach is not None:
            event = MaxDrawdownExceededEvent(
                occurred_at=at,
                current_drawdown=drawdown,
                limit=self.limits.max_drawdown,
            )
            return new_state._raise(event)

        return new_state
