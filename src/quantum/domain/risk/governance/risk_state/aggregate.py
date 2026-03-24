from collections.abc import Mapping
from decimal import Decimal

from quantum.domain.risk.governance.limits.risk_limits import RiskLimits
from quantum.domain.risk.governance.measures.daily_loss import DailyLoss
from quantum.domain.risk.governance.measures.drawdown import Drawdown
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.risk.governance.measures.exposure import Exposure
from quantum.domain.risk.governance.measures.notional import Notional
from quantum.domain.risk.governance.risk_state.breaches.daily_loss_breach import (
    DailyLossBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.drawdown_breach import (
    DrawdownBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.exposure_breach import (
    ExposureBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.leverage_breach import (
    LeverageBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.notional_breach import (
    NotionalBreach,
)
from quantum.domain.risk.governance.risk_state.events.equity_adjusted_event import (
    EquityAdjustedEvent,
)
from quantum.domain.risk.governance.risk_state.events.risk_breach_detected_event import (
    RiskBreachDetectedEvent,
)
from quantum.domain.risk.governance.risk_state.events.risk_initialized_event import (
    RiskInitializedEvent,
)
from quantum.domain.risk.governance.risk_state.risk_state_id import RiskStateId
from quantum.domain.risk.governance.risk_state.states.risk_initialized_state import (
    RiskInitializedState,
)
from quantum.domain.risk.governance.risk_state.states.risk_state_base import (
    RiskStateBase,
)
from quantum.domain.risk.governance.risk_state.states.risk_uninitialized_state import (
    RiskUninitializedState,
)
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


class RiskState(EventSourcedAggregateRoot[RiskStateId, RiskStateBase]):
    """
    This aggregate is the SINGLE SOURCE OF TRUTH for:
    - RiskLimits configuration
    - Equity evolution
    - Equity peak tracking
    - Risk breach detection

    HARD GUARANTEES:
    - Fully deterministic replay
    - No hidden mutation
    - All governance logic event-sourced
    - All invariants enforced at aggregate boundary
    - No implicit initialization
    - No state corruption possible
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[RiskStateId]:
        return RiskStateId

    @classmethod
    def state_type(cls) -> type[RiskStateBase]:
        return RiskStateBase

    @classmethod
    def uninitialized_state(cls) -> RiskStateBase:
        return RiskUninitializedState(
            last_sequence=EventSequence.initial(),
        )

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

        if initial_equity.context != limits.context:
            raise InvariantViolation(
                "Initial equity MoneyContext mismatch with RiskLimits"
            )

        return [
            RiskInitializedEvent(
                limits=limits,
                initial_equity=initial_equity,
            )
        ]

    # --- Commands -------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        *,
        state: RiskInitializedState,
        pnl: RealizedPnL,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
    ) -> None:

        limits = state.limits

        if pnl.context != limits.context:
            raise InvariantViolation("PnL MoneyContext mismatch")

        if daily_loss.context != limits.context:
            raise InvariantViolation("DailyLoss MoneyContext mismatch")

        if exposure.context != limits.context:
            raise InvariantViolation("Exposure MoneyContext mismatch")

        if notional.context != limits.context:
            raise InvariantViolation("Notional MoneyContext mismatch")

        if pnl.currency != state.equity.currency:
            raise CurrencyMismatch("PnL currency mismatch")

        if exposure.currency != state.equity.currency:
            raise CurrencyMismatch("Exposure currency mismatch")

        if notional.currency != state.equity.currency:
            raise CurrencyMismatch("Notional currency mismatch")

    @staticmethod
    def _compute_equity_and_drawdown(
        *,
        state: RiskInitializedState,
        pnl: RealizedPnL,
    ) -> tuple[Equity, Equity, Drawdown]:

        new_equity = state.equity.add(pnl)
        new_peak = max(state.equity_peak, new_equity, key=lambda e: e.value)
        drawdown_value = new_peak.value - new_equity.value

        if drawdown_value < Decimal("0"):
            raise InvariantViolation("Drawdown cannot be negative")

        drawdown = Drawdown(
            value=drawdown_value,
            currency=new_equity.currency,
            context=new_equity.context,
        )

        return new_equity, new_peak, drawdown

    @staticmethod
    def _detect_breach_events(
        *,
        state: RiskInitializedState,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
        new_equity: Equity,
    ) -> list[BaseEvent]:

        limits = state.limits

        breaches = [
            DrawdownBreach.detect(
                current=drawdown,
                limit=limits.max_drawdown,
                policy=limits.threshold_policy,
            ),
            DailyLossBreach.detect(
                current=daily_loss,
                limit=limits.max_daily_loss,
                policy=limits.threshold_policy,
            ),
            ExposureBreach.detect(
                current=exposure,
                limit=limits.max_exposure,
                policy=limits.threshold_policy,
            ),
            NotionalBreach.detect(
                current=notional,
                limit=limits.max_notional,
                policy=limits.threshold_policy,
            ),
            LeverageBreach.detect(
                exposure=exposure,
                equity=new_equity,
                limit=limits.max_leverage,
                policy=limits.threshold_policy,
            ),
        ]

        return [RiskBreachDetectedEvent(breach=b) for b in breaches if b is not None]

    def register_pnl(
        self,
        *,
        pnl: RealizedPnL,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
    ) -> list[BaseEvent]:
        """
        Registers a realized PnL, updates equity & peak, and detects breaches.
        """

        state = self.state

        if not isinstance(state, RiskInitializedState):
            raise InvalidStateTransition("RiskState not initialized")

        # --- Strict MoneyContext and currency validation
        self._validate_inputs(
            state=state,
            pnl=pnl,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
        )

        new_equity, new_peak, drawdown = self._compute_equity_and_drawdown(
            state=state,
            pnl=pnl,
        )

        events: list[BaseEvent] = [
            EquityAdjustedEvent(
                pnl=pnl,
                new_equity=new_equity,
                new_equity_peak=new_peak,
            )
        ]

        # --- Risk breach detection
        breach_events = self._detect_breach_events(
            state=state,
            drawdown=drawdown,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
            new_equity=new_equity,
        )

        return events + breach_events

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_initialized(
        state: RiskStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskStateBase:

        if not isinstance(event, RiskInitializedEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskUninitializedState):
            raise InvalidStateTransition("RiskState already initialized")

        return RiskInitializedState(
            last_sequence=envelope.sequence,
            limits=event.limits,
            equity=event.initial_equity,
            equity_peak=event.initial_equity,
        )

    @staticmethod
    def _apply_equity_adjusted(
        state: RiskStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskStateBase:

        if not isinstance(event, EquityAdjustedEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskInitializedState):
            raise InvalidStateTransition(
                "Cannot apply EquityAdjustedEvent before initialization"
            )

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
        envelope: RecordedEventEnvelope,
    ) -> RiskStateBase:

        if not isinstance(event, RiskBreachDetectedEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskInitializedState):
            raise InvalidStateTransition("RiskState not initialized")

        return RiskInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            equity=state.equity,
            equity_peak=state.equity_peak,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[RiskStateBase, BaseEvent]]:
        return {
            RiskInitializedEvent: cls._apply_initialized,
            EquityAdjustedEvent: cls._apply_equity_adjusted,
            RiskBreachDetectedEvent: cls._apply_breach,
        }
