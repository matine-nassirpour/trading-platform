from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from quantum.domain.events.risk.v1.max_drawdown_exceeded_event import (
    MaxDrawdownExceededEvent,
)
from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions import InvariantViolation
from quantum.domain.model.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class RiskState(AggregateRoot):
    max_drawdown: DrawdownLimit
    current_drawdown: Money

    def __post_init__(self) -> None:
        if self.current_drawdown.value > Decimal("0"):
            raise InvariantViolation("Current drawdown must be ≤ 0")

        if self.current_drawdown.currency != self.max_drawdown.value.currency:
            raise InvariantViolation("Currency mismatch")

    def register_pnl(self, pnl: Money, at: EpochMs):
        if pnl.currency != self.current_drawdown.currency:
            raise InvariantViolation("Currency mismatch")

        if pnl.value >= 0:
            return self

        new_dd = Money(
            self.current_drawdown.value + pnl.value,
            self.current_drawdown.currency,
        )

        new_state = replace(self, current_drawdown=new_dd)

        if new_dd.value <= -self.max_drawdown.value.value:
            event = MaxDrawdownExceededEvent(
                occurred_at=at.to_datetime(),
                current_drawdown=new_dd,
                limit=self.max_drawdown.value,
                trigger_epoch_ms=at,
            )
            return new_state._raise(event)

        return new_state
