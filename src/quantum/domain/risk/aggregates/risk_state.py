from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.risk.events.v1.max_drawdown_exceeded_event import (
    MaxDrawdownExceededEvent,
)
from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.aggregate_root import AggregateRoot
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.money import Money


@dataclass(frozen=True)
class RiskState(AggregateRoot):
    """
    Aggregate Root encapsulating drawdown-based risk constraints.

    Canonical convention:
    - equity_peak >= equity
    - drawdown = equity_peak - equity >= 0
    """

    max_drawdown: DrawdownLimit
    equity: Money
    equity_peak: Money

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        if self.equity.currency != self.equity_peak.currency:
            raise InvariantViolation("Currency mismatch in RiskState")

        if self.max_drawdown.value.currency != self.equity.currency:
            raise InvariantViolation("Drawdown currency mismatch")

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("Equity peak cannot be below current equity")

    # --- Commands -------------------------------------------------------------

    def register_pnl(self, pnl: Money, at: EpochMs) -> RiskState:
        if pnl.currency != self.equity.currency:
            raise InvariantViolation("PnL currency mismatch")

        new_equity = self.equity + pnl

        new_peak = (
            new_equity
            if new_equity.value > self.equity_peak.value
            else self.equity_peak
        )

        drawdown_value = new_peak.value - new_equity.value  # ALWAYS >= 0

        new_state = replace(
            self,
            equity=new_equity,
            equity_peak=new_peak,
        )

        if drawdown_value >= self.max_drawdown.value.value:
            event = MaxDrawdownExceededEvent(
                occurred_at=at,
                current_drawdown=Drawdown(
                    value=drawdown_value,
                    currency=new_equity.currency,
                ),
                limit=self.max_drawdown.value,
            )
            return new_state._raise(event)

        return new_state
