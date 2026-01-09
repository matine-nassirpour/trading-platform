from __future__ import annotations

from quantum.domain.risk.events.v1.equity_adjusted_event import EquityAdjustedEvent
from quantum.domain.risk.events.v1.max_drawdown_exceeded_event import (
    MaxDrawdownExceededEvent,
)
from quantum.domain.risk.policies.risk_policy import RiskPolicy
from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.equity import Equity
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


class RiskState(EventSourcedAggregateRoot):
    """
    Aggregate Root encapsulating drawdown-based risk constraints.

    Canonical invariants:
    - equity_peak ≥ equity
    - drawdown = equity_peak − equity ≥ 0
    """

    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def initialize(*, limits: RiskLimits, equity: Equity) -> RiskState:
        rs = RiskState.__new__(RiskState)
        EventSourcedAggregateRoot.__init__(rs)

        rs.limits = limits
        rs.equity = equity
        rs.equity_peak = equity

        rs._validate_state()
        return rs

    # --- Commands -------------------------------------------------------------

    def register_pnl(self, *, pnl: RealizedPnL, at: EpochMs) -> None:
        """
        Registers a realized PnL.
        """

        if pnl.context != self.equity.context:
            raise InvariantViolation("MoneyContext mismatch")

        if pnl.currency != self.equity.currency:
            raise InvariantViolation("PnL currency mismatch")

        new_equity: Equity = self.equity.add(pnl)
        new_equity_peak: Equity = max(
            self.equity_peak, new_equity, key=lambda e: e.value
        )

        future_drawdown = Drawdown(
            value=new_equity_peak.value - new_equity.value,
            currency=new_equity.currency,
            context=new_equity.context,
        )

        drawdown_breach = RiskPolicy.evaluate_drawdown(
            current_drawdown=future_drawdown,
            limits=self.limits,
        )

        self._raise(
            EquityAdjustedEvent(
                occurred_at=at,
                pnl=pnl,
                new_equity=new_equity,
                new_equity_peak=new_equity_peak,
            )
        )

        if drawdown_breach is not None:
            self._raise(
                MaxDrawdownExceededEvent(
                    occurred_at=at,
                    current_drawdown=future_drawdown,
                    limit=self.limits.max_drawdown,
                )
            )

    # --- Event application ----------------------------------------------------

    def _apply_equityadjustedevent(self, event: EquityAdjustedEvent) -> None:
        self.equity = event.new_equity
        self.equity_peak = event.new_equity_peak

    def _apply_maxdrawdownexceededevent(self, event: MaxDrawdownExceededEvent) -> None:
        # Governance event only → no state change
        pass

    # --- Invariants -----------------------------------------------------------

    def _validate_state(self) -> None:
        if self.equity.currency != self.equity_peak.currency:
            raise InvariantViolation("Currency mismatch in RiskState")

        if self.limits.max_drawdown.currency != self.equity.currency:
            raise InvariantViolation("Drawdown currency mismatch")

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("Equity peak cannot be below current equity")
