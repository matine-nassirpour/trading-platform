from collections.abc import Mapping

from quantum.domain.market.calendar.utc_date import UtcDate
from quantum.domain.risk_governance.breach_detection.risk_breach_detector import (
    RiskBreachDetector,
)
from quantum.domain.risk_governance.lifecycle.events.realized_pnl_registered_event import (
    RealizedPnLRegisteredEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_breaches_cleared_event import (
    RiskBreachesClearedEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_breaches_detected_event import (
    RiskBreachesDetectedEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_governance_initialized_event import (
    RiskGovernanceInitializedEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_governance_insolvency_declared_event import (
    RiskGovernanceInsolvencyDeclaredEvent,
)
from quantum.domain.risk_governance.lifecycle.events.risk_trading_day_reset_event import (
    RiskTradingDayResetEvent,
)
from quantum.domain.risk_governance.lifecycle.states.risk_governance_initialized_state import (
    RiskGovernanceInitializedState,
)
from quantum.domain.risk_governance.lifecycle.states.risk_governance_insolvent_state import (
    RiskGovernanceInsolventState,
)
from quantum.domain.risk_governance.lifecycle.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.lifecycle.states.risk_governance_uninitialized_state import (
    RiskGovernanceUninitializedState,
)
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.portfolio_state.evolution.daily_loss_evolution import (
    DailyLossEvolutionService,
)
from quantum.domain.risk_governance.portfolio_state.evolution.risk_snapshot_evolution import (
    RiskSnapshotEvolutionService,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId
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
        *, limits: RiskLimits, initial_snapshot: RiskSnapshot, trading_day: UtcDate
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
                trading_day=trading_day,
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

        snapshot_evolution = RiskSnapshotEvolutionService.evolve_after_realized_pnl(
            current_snapshot=state.snapshot,
            pnl=pnl,
        )

        new_snapshot = snapshot_evolution.snapshot

        detection = RiskBreachDetector.detect(
            limits=state.limits,
            drawdown=new_snapshot.drawdown,
            daily_loss=new_snapshot.daily_loss,
            exposure=new_snapshot.exposure,
            notional=new_snapshot.notional,
            equity=new_snapshot.equity,
        )

        events: list[BaseEvent] = [
            RealizedPnLRegisteredEvent(
                pnl=pnl,
                resulting_snapshot=new_snapshot,
            ),
        ]

        if new_snapshot.equity.value <= 0:
            events.append(
                RiskGovernanceInsolvencyDeclaredEvent(
                    snapshot=new_snapshot,
                )
            )

        if detection.breaches:
            events.append(
                RiskBreachesDetectedEvent(
                    breaches=detection.breaches,
                )
            )
        elif state.active_breaches:
            events.append(RiskBreachesClearedEvent())

        return events

    def reset_trading_day(self, *, trading_day: UtcDate) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition("RiskGovernance not initialized")

        if isinstance(state, RiskGovernanceInsolventState):
            raise InvalidStateTransition(
                "Cannot reset trading day on insolvent governance"
            )

        if trading_day == state.trading_day:
            return []

        return [
            RiskTradingDayResetEvent(
                trading_day=trading_day,
            )
        ]

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
            trading_day=event.trading_day,
            active_breaches=(),
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

        if event.resulting_snapshot.equity.context != state.limits.context:
            raise InvariantViolation(
                "Resulting RiskSnapshot MoneyContext mismatch with RiskLimits"
            )

        if (
            event.resulting_snapshot.equity.currency
            != state.limits.context.reporting_currency
        ):
            raise CurrencyMismatch(
                "Resulting RiskSnapshot currency must equal RiskLimits.context.reporting_currency"
            )

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=event.resulting_snapshot,
            trading_day=state.trading_day,
            active_breaches=state.active_breaches,
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
            trading_day=state.trading_day,
            active_breaches=event.breaches,
        )

    @staticmethod
    def _apply_risk_breaches_cleared(
        state: RiskGovernanceStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskGovernanceStateBase:
        if not isinstance(event, RiskBreachesClearedEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition(
                "Cannot apply RiskBreachesClearedEvent before initialization"
            )

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=state.snapshot,
            trading_day=state.trading_day,
            active_breaches=(),
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

        if isinstance(state, RiskGovernanceInsolventState):
            raise InvalidStateTransition("RiskGovernance is already insolvent")

        if event.snapshot.equity.value > 0:
            raise InvalidStateTransition(
                "Cannot declare insolvency with positive equity"
            )

        if event.snapshot.equity.context != state.limits.context:
            raise InvariantViolation(
                "Insolvency snapshot MoneyContext mismatch with RiskLimits"
            )

        if event.snapshot.equity.currency != state.limits.context.reporting_currency:
            raise CurrencyMismatch(
                "Insolvency snapshot currency must equal RiskLimits.context.reporting_currency"
            )

        return RiskGovernanceInsolventState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=event.snapshot,
            trading_day=state.trading_day,
            active_breaches=state.active_breaches,
        )

    @staticmethod
    def _apply_trading_day_reset(
        state: RiskGovernanceStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> RiskGovernanceStateBase:
        if not isinstance(event, RiskTradingDayResetEvent):
            raise InvariantViolation("Invalid event type")

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition(
                "Cannot reset trading day before initialization"
            )

        new_daily_loss = DailyLossEvolutionService.reset(
            current_daily_loss=state.snapshot.daily_loss,
        )

        new_snapshot = RiskSnapshot(
            equity=state.snapshot.equity,
            equity_peak=state.snapshot.equity_peak,
            drawdown=state.snapshot.drawdown,
            daily_loss=new_daily_loss,
            exposure=state.snapshot.exposure,
            notional=state.snapshot.notional,
        )

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            snapshot=new_snapshot,
            trading_day=event.trading_day,
            active_breaches=(),
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
            RiskBreachesClearedEvent: cls._apply_risk_breaches_cleared,
            RiskTradingDayResetEvent: cls._apply_trading_day_reset,
        }
