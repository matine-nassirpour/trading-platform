from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType

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
from quantum.domain.risk.events.v1.risk_initialized_event import RiskInitializedEvent
from quantum.domain.risk.governance.aggregates.risk_initialized_state import (
    RiskInitializedState,
)
from quantum.domain.risk.governance.aggregates.risk_state_base import RiskStateBase
from quantum.domain.risk.governance.aggregates.risk_uninitialized_state import (
    RiskUninitializedState,
)
from quantum.domain.risk.limits.risk_limits import RiskLimits
from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.money.daily_loss import DailyLoss
from quantum.domain.shared_kernel.money.drawdown import Drawdown
from quantum.domain.shared_kernel.money.equity import Equity
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.pnl import RealizedPnL


class RiskState(EventSourcedAggregateRoot[RiskStateBase]):
    """
    Event-sourced aggregate implementing drawdown-based risk governance.

    SOURCE OF TRUTH:
    - limits are established ONLY by RiskInitializedEvent
    - equity evolution is driven ONLY by EquityAdjustedEvent
    - detected breaches are facts in the stream (RiskBreachDetectedEvent)

    HARD INVARIANTS (enforced in RiskInitializedState):
    - equity_peak >= equity
    - all monetary values share the same MoneyContext (and currency where applicable)
    """

    __slots__ = ()

    @classmethod
    def empty_state(cls) -> RiskStateBase:
        return RiskUninitializedState(last_sequence=EventSequence.initial())

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def initialize(
        *,
        limits: RiskLimits,
        initial_equity: Equity,
    ) -> list[BaseEvent]:
        """
        Creates the canonical initialization event(s).

        NOTE:
        - Initialization MUST be represented by an explicit event in the stream.
        - limits MUST be event-sourced to preserve auditability and deterministic replay.
        """

        return [
            RiskInitializedEvent(
                limits=limits,
                initial_equity=initial_equity,
            )
        ]

    # --- Commands -------------------------------------------------------------

    def register_pnl(
        self,
        *,
        pnl: RealizedPnL,
        daily_loss: DailyLoss,
        exposure: RiskExposure,
        notional: Notional,
    ) -> list[BaseEvent]:
        """
        Registers a realized PnL, updates equity & peak, and detects breaches.

        IMPORTANT (high assurance):
        - drawdown is computed internally from (equity_peak, equity)
          to ensure deterministic governance.
        - external measurements (daily_loss/exposure/notional) are accepted as
          observations but are type-checked and context/currency-checked.
        """

        state = self.state

        if not isinstance(state, RiskInitializedState):
            raise InvalidStateTransition("RiskState not initialized")

        new_equity = state.equity.add(pnl)
        new_peak = max(state.equity_peak, new_equity, key=lambda e: e.value)

        # Internal drawdown = peak - equity (always >= 0 by invariant + construction)
        drawdown_value = new_peak.value - new_equity.value
        if drawdown_value < Decimal("0"):
            # Defensive: should be impossible if max() above is correct.
            raise InvariantViolation("Computed drawdown must be non-negative")

        drawdown = Drawdown(
            value=drawdown_value,
            currency=new_equity.currency,
            context=new_equity.context,
        )

        events: list[BaseEvent] = [
            EquityAdjustedEvent(
                pnl=pnl,
                new_equity=new_equity,
                new_equity_peak=new_peak,
            )
        ]

        breach: RiskBreach | None

        breach = DrawdownBreach.detect(
            current=drawdown,
            limit=state.limits.max_drawdown,
            policy=state.limits.threshold_policy,
        )
        if breach is not None:
            events.append(RiskBreachDetectedEvent(breach=breach))

        breach = DailyLossBreach.detect(
            current=daily_loss,
            limit=state.limits.max_daily_loss,
            policy=state.limits.threshold_policy,
        )
        if breach is not None:
            events.append(RiskBreachDetectedEvent(breach=breach))

        breach = ExposureBreach.detect(
            current=exposure,
            limit=state.limits.max_exposure,
            policy=state.limits.threshold_policy,
        )
        if breach is not None:
            events.append(RiskBreachDetectedEvent(breach=breach))

        breach = NotionalBreach.detect(
            current=notional,
            limit=state.limits.max_notional,
            policy=state.limits.threshold_policy,
        )
        if breach is not None:
            events.append(RiskBreachDetectedEvent(breach=breach))

        breach = LeverageBreach.detect(
            exposure=exposure,
            equity=new_equity,
            limit=state.limits.max_leverage,
            policy=state.limits.threshold_policy,
        )
        if breach is not None:
            events.append(RiskBreachDetectedEvent(breach=breach))

        return events

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_equity_adjusted(
        state: RiskStateBase,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> RiskStateBase:

        assert isinstance(event, EquityAdjustedEvent)

        if isinstance(state, RiskUninitializedState):
            return RiskInitializedState(
                last_sequence=envelope.sequence,
                limits=state.limits,
                equity=event.new_equity,
                equity_peak=event.new_equity_peak,
            )

        assert isinstance(state, RiskInitializedState)

        return RiskInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            equity=event.new_equity,
            equity_peak=event.new_equity_peak,
        )

    @staticmethod
    def _apply_breach(
        state: RiskStateBase,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> RiskStateBase:

        assert isinstance(state, RiskInitializedState)
        assert isinstance(event, RiskBreachDetectedEvent)

        return RiskInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            equity=state.equity,
            equity_peak=state.equity_peak,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler]:

        return MappingProxyType(
            {
                EquityAdjustedEvent: cls._apply_equity_adjusted,
                RiskBreachDetectedEvent: cls._apply_breach,
            }
        )
