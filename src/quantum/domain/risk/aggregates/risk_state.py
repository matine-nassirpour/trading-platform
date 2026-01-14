from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.events.v1.equity_adjusted_event import EquityAdjustedEvent
from quantum.domain.risk.events.v1.max_drawdown_exceeded_event import (
    MaxDrawdownExceededEvent,
)
from quantum.domain.risk.policies.risk_policy import RiskPolicy
from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.equity import Equity
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RiskStateData(AggregateState):
    """
    Fully event-sourced immutable state of RiskState.

    All invariants must be preserved by event application.
    """

    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    def _state_contract(self) -> None:
        pass


class RiskState(EventSourcedAggregateRoot[RiskStateData]):
    """
    Event-sourced aggregate implementing drawdown-based risk governance.

    Invariants:
    - equity_peak >= equity
    - drawdown = equity_peak − equity >= 0
    - all monetary values share the same MoneyContext
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def initialize(*, limits: RiskLimits, initial_equity: Equity) -> RiskState:
        """
        Creates the initial RiskState.

        This is NOT state injection – this produces the canonical empty state
        and lets the first EquityAdjustedEvent establish the state.
        """

        empty = RiskStateData(
            limits=limits,
            equity=initial_equity,
            equity_peak=initial_equity,
        )

        return RiskState(empty)

    # --- Commands -------------------------------------------------------------

    def register_pnl(self, *, pnl: RealizedPnL) -> list:
        """
        Registers a realized PnL.

        Returns the list of domain events that must be persisted and applied.
        """

        state = self.state

        if pnl.context != state.equity.context:
            raise InvariantViolation("MoneyContext mismatch")

        if pnl.currency != state.equity.currency:
            raise InvariantViolation("PnL currency mismatch")

        new_equity = state.equity.add(pnl)
        new_peak = max(state.equity_peak, new_equity, key=lambda e: e.value)

        future_drawdown = Drawdown(
            value=new_peak.value - new_equity.value,
            currency=new_equity.currency,
            context=new_equity.context,
        )

        events = [
            EquityAdjustedEvent(
                pnl=pnl,
                new_equity=new_equity,
                new_equity_peak=new_peak,
            )
        ]

        breach = RiskPolicy.evaluate_drawdown(
            current_drawdown=future_drawdown,
            limits=state.limits,
        )

        if breach is not None:
            events.append(
                MaxDrawdownExceededEvent(
                    current_drawdown=future_drawdown,
                    limit=state.limits.max_drawdown,
                )
            )

        return events

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_equity_adjusted(
        state: RiskStateData,
        event: EquityAdjustedEvent,
    ) -> RiskStateData:
        return RiskStateData(
            limits=state.limits,
            equity=event.new_equity,
            equity_peak=event.new_equity_peak,
        )

    @staticmethod
    def _apply_drawdown_breached(
        state: RiskStateData,
        event: MaxDrawdownExceededEvent,
    ) -> RiskStateData:
        # Governance event only — no state mutation
        return state

    @classmethod
    def _handlers(cls):
        return {
            EquityAdjustedEvent: cls._apply_equity_adjusted,
            MaxDrawdownExceededEvent: cls._apply_drawdown_breached,
        }

    # --- Invariants -----------------------------------------------------------

    def _validate_state(self) -> None:
        s = self.state

        if s.equity.currency != s.equity_peak.currency:
            raise InvariantViolation("Currency mismatch in RiskState")

        if s.limits.max_drawdown.currency != s.equity.currency:
            raise InvariantViolation("Drawdown currency mismatch")

        if s.equity_peak.value < s.equity.value:
            raise InvariantViolation("Equity peak cannot be below current equity")
