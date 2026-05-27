from collections.abc import Mapping

from quantum.domain.risk_governance.events.realized_pnl_registered_event import (
    RealizedPnLRegisteredEvent,
)
from quantum.domain.risk_governance.events.risk_breaches_detected_event import (
    RiskBreachesDetectedEvent,
)
from quantum.domain.risk_governance.events.risk_governance_initialized_event import (
    RiskGovernanceInitializedEvent,
)
from quantum.domain.risk_governance.events.risk_governance_insolvency_declared_event import (
    RiskGovernanceInsolvencyDeclaredEvent,
)
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId
from quantum.domain.risk_governance.services.daily_loss_evolution import (
    DailyLossEvolutionService,
)
from quantum.domain.risk_governance.services.equity_evolution import (
    EquityEvolutionService,
)
from quantum.domain.risk_governance.services.risk_breach_detector import (
    RiskBreachDetector,
)
from quantum.domain.risk_governance.states.risk_governance_initialized_state import (
    RiskGovernanceInitializedState,
)
from quantum.domain.risk_governance.states.risk_governance_insolvent_state import (
    RiskGovernanceInsolventState,
)
from quantum.domain.risk_governance.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.states.risk_governance_uninitialized_state import (
    RiskGovernanceUninitializedState,
)
from quantum.domain.risk_governance.states.risk_snapshot import RiskSnapshot
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


class RiskGovernance(
    EventSourcedAggregateRoot[RiskGovernanceId, RiskGovernanceStateBase]
):
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
    def aggregate_id_type(cls) -> type[RiskGovernanceId]:
        return RiskGovernanceId

    @classmethod
    def state_type(cls) -> type[RiskGovernanceStateBase]:
        return RiskGovernanceStateBase

    @classmethod
    def uninitialized_state(cls) -> RiskGovernanceStateBase:
        return RiskGovernanceUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def initialize(
        *,
        limits: RiskLimits,
        initial_snapshot: RiskSnapshot,
    ) -> list[BaseEvent]:
        """
        Creates the canonical initialization event(s).

        Initialization MUST be represented by an explicit event in the stream.
        """

        if initial_snapshot.equity.context != limits.context:
            raise InvariantViolation(
                "Initial RiskSnapshot MoneyContext mismatch with RiskLimits"
            )

        if initial_snapshot.equity.currency != limits.context.reporting_currency:
            raise CurrencyMismatch(
                "Initial RiskSnapshot currency must equal "
                "RiskLimits.context.reporting_currency"
            )

        return [
            RiskGovernanceInitializedEvent(
                limits=limits,
                initial_snapshot=initial_snapshot,
            )
        ]

    # --- Commands -------------------------------------------------------------
    def register_pnl(self, *, pnl: RealizedPnL) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition("RiskGovernance not initialized")

        if isinstance(state, RiskGovernanceInsolventState):
            raise InvalidStateTransition(
                "RiskGovernance is insolvent; further PnL registration is forbidden"
            )

        if pnl.context != state.limits.context:
            raise InvariantViolation("PnL MoneyContext mismatch")

        if pnl.currency != state.limits.context.reporting_currency:
            raise CurrencyMismatch(
                "PnL currency must equal RiskLimits.context.reporting_currency"
            )

        evolution = EquityEvolutionService.evolve(
            current_equity=state.snapshot.equity,
            current_peak=state.snapshot.equity_peak,
            pnl=pnl,
        )

        new_daily_loss = DailyLossEvolutionService.evolve(
            current_daily_loss=state.snapshot.daily_loss,
            pnl=pnl,
        )

        new_snapshot = RiskSnapshot(
            equity=evolution.new_equity,
            equity_peak=evolution.new_equity_peak,
            drawdown=evolution.drawdown,
            daily_loss=new_daily_loss,
            exposure=state.snapshot.exposure,
            notional=state.snapshot.notional,
        )

        detection = RiskBreachDetector.detect(
            limits=state.limits,
            drawdown=new_snapshot.drawdown,
            daily_loss=new_snapshot.daily_loss,
            exposure=new_snapshot.exposure,
            notional=new_snapshot.notional,
            equity=new_snapshot.equity,
        )

        events: list[BaseEvent] = [
            RealizedPnLRegisteredEvent(pnl=pnl),
        ]

        if new_snapshot.equity.value <= 0:
            events.append(
                RiskGovernanceInsolvencyDeclaredEvent(
                    equity=new_snapshot.equity,
                )
            )

        if detection.breaches:
            events.append(
                RiskBreachesDetectedEvent(
                    breaches=detection.breaches,
                )
            )

        return events

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_initialized(
        state: RiskGovernanceStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskGovernanceStateBase:
        if not isinstance(event, RiskGovernanceInitializedEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskGovernanceUninitializedState):
            raise InvalidStateTransition("RiskGovernance already initialized")

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=event.limits,
            snapshot=event.initial_snapshot,
        )

    @staticmethod
    def _apply_realized_pnl_registered(
        state: RiskGovernanceStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskGovernanceStateBase:
        if not isinstance(event, RealizedPnLRegisteredEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition(
                "Cannot apply RealizedPnLRegisteredEvent before initialization"
            )

        evolution = EquityEvolutionService.evolve(
            current_equity=state.snapshot.equity,
            current_peak=state.snapshot.equity_peak,
            pnl=event.pnl,
        )

        new_daily_loss = DailyLossEvolutionService.evolve(
            current_daily_loss=state.snapshot.daily_loss,
            pnl=event.pnl,
        )

        new_snapshot = RiskSnapshot(
            equity=evolution.new_equity,
            equity_peak=evolution.new_equity_peak,
            drawdown=evolution.drawdown,
            daily_loss=new_daily_loss,
            exposure=state.snapshot.exposure,
            notional=state.snapshot.notional,
        )

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=new_snapshot,
        )

    @staticmethod
    def _apply_insolvency_declared(
        state: RiskGovernanceStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskGovernanceStateBase:
        if not isinstance(event, RiskGovernanceInsolvencyDeclaredEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition(
                "Cannot declare insolvency before initialization"
            )

        if state.snapshot.equity.value > 0:
            raise InvalidStateTransition(
                "Cannot declare insolvency while equity is positive"
            )

        return RiskGovernanceInsolventState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=state.snapshot,
        )

    @staticmethod
    def _apply_risk_breaches_detected(
        state: RiskGovernanceStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskGovernanceStateBase:
        if not isinstance(event, RiskBreachesDetectedEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition(
                "Cannot apply RiskBreachesDetectedEvent before initialization"
            )

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=state.snapshot,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[RiskGovernanceStateBase, BaseEvent]]:
        return {
            RiskGovernanceInitializedEvent: cls._apply_initialized,
            RealizedPnLRegisteredEvent: cls._apply_realized_pnl_registered,
            RiskGovernanceInsolvencyDeclaredEvent: cls._apply_insolvency_declared,
            RiskBreachesDetectedEvent: cls._apply_risk_breaches_detected,
        }
