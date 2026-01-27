from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.risk.breaches.daily_loss_breach import DailyLossBreach
from quantum.domain.risk.breaches.drawdown_breach import DrawdownBreach
from quantum.domain.risk.breaches.exposure_breach import ExposureBreach
from quantum.domain.risk.breaches.leverage_breach import LeverageBreach
from quantum.domain.risk.breaches.notional_breach import NotionalBreach
from quantum.domain.risk.breaches.risk_breach import RiskBreach
from quantum.domain.risk.events.v1.equity_adjusted_event import EquityAdjustedEvent
from quantum.domain.risk.events.v1.risk_breach_detected_event import (
    RiskBreachDetectedEvent,
)
from quantum.domain.risk.limits.risk_limits import RiskLimits
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.money.daily_loss import DailyLoss
from quantum.domain.shared_kernel.money.drawdown import Drawdown
from quantum.domain.shared_kernel.money.equity import Equity
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RiskStateData(AggregateState):
    """
    Fully event-sourced immutable state of the Risk aggregate.

    Invariants:
    - equity_peak >= equity
    - drawdown = equity_peak - equity >= 0
    - all monetary values share the same MoneyContext
    - last_sequence is monotonic
    """

    last_sequence: EventSequence
    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate(self) -> None:
        # Sequence must exist
        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation(
                "RiskStateData.last_sequence must be EventSequence"
            )

        # Context & currency consistency
        if self.equity.currency != self.equity_peak.currency:
            raise InvariantViolation("Equity and EquityPeak currency mismatch")

        if self.equity.context != self.equity_peak.context:
            raise InvariantViolation("Equity and EquityPeak MoneyContext mismatch")

        if self.limits.context != self.equity.context:
            raise InvariantViolation("RiskLimits MoneyContext mismatch")

        # Drawdown invariant
        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("Equity peak cannot be below current equity")


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
        Creates the initial RiskState with sequence = 0.

        This is NOT state injection – this produces the canonical empty state
        and lets the first EquityAdjustedEvent establish the state.
        """

        empty = RiskStateData(
            last_sequence=EventSequence.initial(),
            limits=limits,
            equity=initial_equity,
            equity_peak=initial_equity,
        )

        return RiskState(empty)

    # --- Commands -------------------------------------------------------------

    def register_pnl(
        self,
        *,
        pnl: RealizedPnL,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: RiskExposure,
        notional: Notional,
    ) -> list[BaseEvent]:
        """
        Registers a realized PnL.

        Returns the list of domain events that must be persisted and applied.
        """

        state = self.state

        if pnl.context != state.equity.context:
            raise InvariantViolation("MoneyContext mismatch")

        if pnl.currency != state.equity.currency:
            raise InvariantViolation("Currency mismatch")

        new_equity = state.equity.add(pnl)
        new_peak = max(state.equity_peak, new_equity, key=lambda e: e.value)

        events: list[BaseEvent] = [
            EquityAdjustedEvent(
                pnl=pnl,
                new_equity=new_equity,
                new_equity_peak=new_peak,
            )
        ]

        breach: RiskBreach | None = None

        if breach := DrawdownBreach.detect(
            current=drawdown,
            limit=state.limits.max_drawdown,
            policy=state.limits.threshold_policy,
        ):
            events.append(RiskBreachDetectedEvent(breach=breach))

        if breach := DailyLossBreach.detect(
            current=daily_loss,
            limit=state.limits.max_daily_loss,
            policy=state.limits.threshold_policy,
        ):
            events.append(RiskBreachDetectedEvent(breach=breach))

        if breach := ExposureBreach.detect(
            current=exposure,
            limit=state.limits.max_exposure,
            policy=state.limits.threshold_policy,
        ):
            events.append(RiskBreachDetectedEvent(breach=breach))

        if breach := NotionalBreach.detect(
            current=notional,
            limit=state.limits.max_notional,
            policy=state.limits.threshold_policy,
        ):
            events.append(RiskBreachDetectedEvent(breach=breach))

        if breach := LeverageBreach.detect(
            exposure=exposure,
            equity=new_equity,
            limit=state.limits.max_leverage,
            policy=state.limits.threshold_policy,
        ):
            events.append(RiskBreachDetectedEvent(breach=breach))

        return events

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_equity_adjusted(
        state: RiskStateData,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> RiskStateData:
        assert isinstance(event, EquityAdjustedEvent)
        return RiskStateData(
            last_sequence=envelope.sequence,
            limits=state.limits,
            equity=event.new_equity,
            equity_peak=event.new_equity_peak,
        )

    @staticmethod
    def _apply_breach(
        state: RiskStateData,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> RiskStateData:
        assert isinstance(event, RiskBreachDetectedEvent)
        return RiskStateData(
            last_sequence=envelope.sequence,
            limits=state.limits,
            equity=state.equity,
            equity_peak=state.equity_peak,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[
        type[BaseEvent],
        EventHandler[RiskStateData, BaseEvent],
    ]:
        return {
            EquityAdjustedEvent: cls._apply_equity_adjusted,
            RiskBreachDetectedEvent: cls._apply_breach,
        }
