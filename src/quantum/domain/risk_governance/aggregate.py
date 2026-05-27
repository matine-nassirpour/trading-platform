from collections.abc import Mapping

from quantum.domain.risk_governance.events.realized_pnl_registred_event import (
    RealizedPnLRegisteredEvent,
)
from quantum.domain.risk_governance.events.risk_governance_initialized_event import (
    RiskGovernanceInitializedEvent,
)
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId
from quantum.domain.risk_governance.services.equity_evolution import (
    EquityEvolutionService,
)
from quantum.domain.risk_governance.states.risk_governance_initialized_state import (
    RiskGovernanceInitializedState,
)
from quantum.domain.risk_governance.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.states.risk_governance_uninitialized_state import (
    RiskGovernanceUninitializedState,
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
            RiskGovernanceInitializedEvent(
                limits=limits,
                initial_equity=initial_equity,
            )
        ]

    # --- Commands -------------------------------------------------------------
    def register_pnl(self, *, pnl: RealizedPnL) -> list[BaseEvent]:

        state = self.state

        if not isinstance(state, RiskGovernanceInitializedState):
            raise InvalidStateTransition("RiskGovernance not initialized")

        if pnl.context != state.limits.context:
            raise InvariantViolation("PnL MoneyContext mismatch")

        if pnl.currency != state.limits.context.reporting_currency:
            raise CurrencyMismatch(
                "PnL currency must equal RiskLimits.context.reporting_currency"
            )

        return [RealizedPnLRegisteredEvent(pnl=pnl)]

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
            equity=event.initial_equity,
            equity_peak=event.initial_equity,
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
            current_equity=state.equity,
            current_peak=state.equity_peak,
            pnl=event.pnl,
        )

        return RiskGovernanceInitializedState(
            last_sequence=envelope.sequence,
            limits=state.limits,
            equity=evolution.new_equity,
            equity_peak=evolution.new_equity_peak,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[RiskGovernanceStateBase, BaseEvent]]:
        return {
            RiskGovernanceInitializedEvent: cls._apply_initialized,
            RealizedPnLRegisteredEvent: cls._apply_realized_pnl_registered,
        }
