from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.events.risk.v1.max_drawdown_exceeded_event import (
    MaxDrawdownExceededEvent,
)
from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class RiskState(AggregateRoot):
    """
    Aggregate Root encapsulating drawdown-based risk constraints.
    """

    max_drawdown: DrawdownLimit
    equity: Money
    equity_peak: Money

    # --------------------------------------------------------------------------
    # Invariants
    # --------------------------------------------------------------------------
    def _validate(self) -> None:
        if self.equity.currency != self.equity_peak.currency:
            raise InvariantViolation("Currency mismatch in RiskState")

        if self.max_drawdown.value.currency != self.equity.currency:
            raise InvariantViolation("Drawdown currency mismatch")

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("Equity peak cannot be below current equity")

    # --------------------------------------------------------------------------
    # Commands
    # --------------------------------------------------------------------------
    def register_pnl(self, pnl: Money, at: EpochMs) -> RiskState:
        if pnl.currency != self.equity.currency:
            raise InvariantViolation("PnL currency mismatch")

        new_equity = self.equity + pnl
        new_peak = (
            new_equity
            if new_equity.value > self.equity_peak.value
            else self.equity_peak
        )

        drawdown = new_equity.value - new_peak.value

        new_state = replace(
            self,
            equity=new_equity,
            equity_peak=new_peak,
        )

        if drawdown <= -self.max_drawdown.value.value:
            event = MaxDrawdownExceededEvent(
                occurred_at=at.to_datetime(),
                current_drawdown=Money(drawdown, new_equity.currency),
                limit=self.max_drawdown.value,
                trigger_epoch_ms=at,
            )
            return new_state._raise(event)

        return new_state
