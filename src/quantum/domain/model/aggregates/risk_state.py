from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

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

    Invariants:
    - current_drawdown.value <= 0
    - max_drawdown.value.value > 0
    - currencies must match
    """

    max_drawdown: DrawdownLimit
    current_drawdown: Money

    # --------------------------------------------------------------------------
    # Invariants
    # --------------------------------------------------------------------------
    def _validate(self) -> None:
        if self.current_drawdown.value > Decimal("0"):
            raise InvariantViolation("Current drawdown must be ≤ 0")

        if self.max_drawdown.value.value <= Decimal("0"):
            raise InvariantViolation("Max drawdown must be strictly positive")

        if self.current_drawdown.currency != self.max_drawdown.value.currency:
            raise InvariantViolation("Currency mismatch in RiskState")

    # --------------------------------------------------------------------------
    # Commands
    # --------------------------------------------------------------------------
    def register_pnl(self, pnl: Money, at: EpochMs) -> RiskState:
        """
        Registers a realized PnL delta.

        Rules:
        - Positive PnL does not affect drawdown
        - Negative PnL increases drawdown
        - Emits MaxDrawdownExceededEvent if limit breached
        """
        if pnl.currency != self.current_drawdown.currency:
            raise InvariantViolation("PnL currency mismatch")

        # Gains do not worsen drawdown
        if pnl.value >= Decimal("0"):
            return self

        new_drawdown = Money(
            self.current_drawdown.value + pnl.value,
            self.current_drawdown.currency,
        )

        new_state = replace(self, current_drawdown=new_drawdown)

        if new_drawdown.value <= -self.max_drawdown.value.value:
            event = MaxDrawdownExceededEvent(
                occurred_at=at.to_datetime(),
                current_drawdown=new_drawdown,
                limit=self.max_drawdown.value,
                trigger_epoch_ms=at,
            )
            return new_state._raise(event)

        return new_state
