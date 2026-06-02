from collections.abc import Mapping
from typing import Self

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.position_sizing.lifecycle.events.position_sized_event import (
    PositionSizedEvent,
)
from quantum.domain.position_sizing.lifecycle.events.position_sizing_rejected_event import (
    PositionSizingRejectedEvent,
)
from quantum.domain.position_sizing.lifecycle.events.position_sizing_requested_event import (
    PositionSizingRequestedEvent,
)
from quantum.domain.position_sizing.lifecycle.states.position_sizing_pending_state import (
    PositionSizingPendingState,
)
from quantum.domain.position_sizing.lifecycle.states.position_sizing_rejected_state import (
    PositionSizingRejectedState,
)
from quantum.domain.position_sizing.lifecycle.states.position_sizing_sized_state import (
    PositionSizingSizedState,
)
from quantum.domain.position_sizing.lifecycle.states.position_sizing_state_base import (
    PositionSizingStateBase,
)
from quantum.domain.position_sizing.lifecycle.states.position_sizing_uninitialized_state import (
    PositionSizingUninitializedState,
)
from quantum.domain.position_sizing.model.allocation.sizing_allocation import (
    SizingAllocation,
)
from quantum.domain.position_sizing.model.equity.sizing_equity import SizingEquity
from quantum.domain.position_sizing.model.policies.sizing_rounding_policy import (
    SizingRoundingPolicy,
)
from quantum.domain.position_sizing.model.volume.stop_distance import StopDistance
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId
from quantum.domain.position_sizing.services.position_sizer import PositionSizer
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
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


class PositionSizing(
    EventSourcedAggregateRoot[PositionSizingId, PositionSizingStateBase]
):
    """
    Event-sourced aggregate responsible for one auditable position sizing flow.

    Responsibilities:
    - capture sizing inputs;
    - compute risk-approved position volume;
    - record either sizing success or sizing rejection.

    Explicitly DOES NOT:
    - create orders;
    - execute trades;
    - reserve capital;
    - mutate portfolio state.
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[PositionSizingId]:
        return PositionSizingId

    @classmethod
    def state_type(cls) -> type[PositionSizingStateBase]:
        return PositionSizingStateBase

    @classmethod
    def uninitialized_state(cls) -> PositionSizingStateBase:
        return PositionSizingUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    @staticmethod
    def _assert_event_matches_stream_identity(
        *,
        event_sizing_id: PositionSizingId,
        envelope: RecordedEventEnvelope,
    ) -> None:
        if event_sizing_id != envelope.aggregate_id:
            raise InvariantViolation(
                "Event sizing_id does not match envelope aggregate_id"
            )

    def _require_pending(self) -> PositionSizingPendingState:
        state = self.state

        if isinstance(state, PositionSizingUninitializedState):
            raise InvalidStateTransition("PositionSizing not initialized")

        if isinstance(state, (PositionSizingSizedState, PositionSizingRejectedState)):
            raise InvalidStateTransition("PositionSizing is terminal")

        if not isinstance(state, PositionSizingPendingState):
            raise InvariantViolation("Corrupted PositionSizing state")

        return state

    # --- Creation API ---------------------------------------------------------

    @classmethod
    def decide_request(
        cls,
        *,
        sizing_id: PositionSizingId,
        decision_id: DecisionId,
        strategy_id: StrategyId,
        symbol: Symbol,
        allocation: SizingAllocation,
        equity: SizingEquity,
        stop_distance: StopDistance,
        instrument: InstrumentSpec,
        reference_price: ReferencePrice,
        rounding_policy: SizingRoundingPolicy,
    ) -> list[BaseEvent]:
        return [
            PositionSizingRequestedEvent(
                sizing_id=sizing_id,
                decision_id=decision_id,
                strategy_id=strategy_id,
                symbol=symbol,
                allocation=allocation,
                equity=equity,
                stop_distance=stop_distance,
                instrument=instrument,
                reference_price=reference_price,
                rounding_policy=rounding_policy,
            )
        ]

    @classmethod
    def create_new(
        cls,
        *,
        aggregate_id: PositionSizingId,
        decision_id: DecisionId,
        strategy_id: StrategyId,
        symbol: Symbol,
        allocation: SizingAllocation,
        equity: SizingEquity,
        stop_distance: StopDistance,
        instrument: InstrumentSpec,
        reference_price: ReferencePrice,
        rounding_policy: SizingRoundingPolicy,
    ) -> tuple[Self, list[BaseEvent]]:
        aggregate = cls.new(aggregate_id=aggregate_id)

        events = cls.decide_request(
            sizing_id=aggregate.aggregate_id,
            decision_id=decision_id,
            strategy_id=strategy_id,
            symbol=symbol,
            allocation=allocation,
            equity=equity,
            stop_distance=stop_distance,
            instrument=instrument,
            reference_price=reference_price,
            rounding_policy=rounding_policy,
        )

        return aggregate, events

    # --- Commands -------------------------------------------------------------

    def size(self) -> list[BaseEvent]:
        state = self._require_pending()

        evaluation = PositionSizer.evaluate(
            allocation=state.allocation,
            equity=state.equity,
            stop_distance=state.stop_distance,
            instrument=state.instrument,
            reference_price=state.reference_price,
            rounding_policy=state.rounding_policy,
        )

        if evaluation.is_rejected():
            if evaluation.rejection_reason is None:
                raise InvariantViolation(
                    "Rejected sizing evaluation must define rejection_reason"
                )

            return [
                PositionSizingRejectedEvent(
                    sizing_id=self.aggregate_id,
                    decision_id=state.decision_id,
                    strategy_id=state.strategy_id,
                    reason_code=evaluation.rejection_reason,
                )
            ]

        if evaluation.result is None:
            raise InvariantViolation("Successful sizing evaluation must define result")

        return [
            PositionSizedEvent(
                sizing_id=self.aggregate_id,
                decision_id=state.decision_id,
                strategy_id=state.strategy_id,
                result=evaluation.result,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_requested(
        state: PositionSizingStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> PositionSizingStateBase:
        if not isinstance(state, PositionSizingUninitializedState):
            raise InvariantViolation("PositionSizing already exists")

        if not isinstance(event, PositionSizingRequestedEvent):
            raise InvariantViolation(
                "PositionSizing._apply_requested requires PositionSizingRequestedEvent"
            )

        PositionSizing._assert_event_matches_stream_identity(
            event_sizing_id=event.sizing_id,
            envelope=envelope,
        )

        return PositionSizingPendingState(
            last_sequence=envelope.sequence,
            decision_id=event.decision_id,
            strategy_id=event.strategy_id,
            symbol=event.symbol,
            allocation=event.allocation,
            equity=event.equity,
            stop_distance=event.stop_distance,
            instrument=event.instrument,
            reference_price=event.reference_price,
            rounding_policy=event.rounding_policy,
            requested_at=envelope.occurred_at,
        )

    @staticmethod
    def _apply_sized(
        state: PositionSizingStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> PositionSizingStateBase:
        if not isinstance(state, PositionSizingPendingState):
            raise InvariantViolation("PositionSizing is not pending")

        if not isinstance(event, PositionSizedEvent):
            raise InvariantViolation(
                "PositionSizing._apply_sized requires PositionSizedEvent"
            )

        PositionSizing._assert_event_matches_stream_identity(
            event_sizing_id=event.sizing_id,
            envelope=envelope,
        )

        if event.decision_id != state.decision_id:
            raise InvariantViolation("PositionSizedEvent.decision_id mismatch")

        if event.strategy_id != state.strategy_id:
            raise InvariantViolation("PositionSizedEvent.strategy_id mismatch")

        return PositionSizingSizedState(
            last_sequence=envelope.sequence,
            decision_id=state.decision_id,
            strategy_id=state.strategy_id,
            symbol=state.symbol,
            allocation=state.allocation,
            equity=state.equity,
            stop_distance=state.stop_distance,
            instrument=state.instrument,
            reference_price=state.reference_price,
            rounding_policy=state.rounding_policy,
            requested_at=state.requested_at,
            result=event.result,
            sized_at=envelope.occurred_at,
        )

    @staticmethod
    def _apply_rejected(
        state: PositionSizingStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> PositionSizingStateBase:
        if not isinstance(state, PositionSizingPendingState):
            raise InvariantViolation("PositionSizing is not pending")

        if not isinstance(event, PositionSizingRejectedEvent):
            raise InvariantViolation(
                "PositionSizing._apply_rejected requires PositionSizingRejectedEvent"
            )

        PositionSizing._assert_event_matches_stream_identity(
            event_sizing_id=event.sizing_id,
            envelope=envelope,
        )

        if event.decision_id != state.decision_id:
            raise InvariantViolation("PositionSizingRejectedEvent.decision_id mismatch")

        if event.strategy_id != state.strategy_id:
            raise InvariantViolation("PositionSizingRejectedEvent.strategy_id mismatch")

        return PositionSizingRejectedState(
            last_sequence=envelope.sequence,
            decision_id=state.decision_id,
            strategy_id=state.strategy_id,
            symbol=state.symbol,
            allocation=state.allocation,
            equity=state.equity,
            stop_distance=state.stop_distance,
            instrument=state.instrument,
            reference_price=state.reference_price,
            rounding_policy=state.rounding_policy,
            requested_at=state.requested_at,
            reason_code=event.reason_code,
            rejected_at=envelope.occurred_at,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[PositionSizingStateBase, BaseEvent]]:
        return {
            PositionSizingRequestedEvent: cls._apply_requested,
            PositionSizedEvent: cls._apply_sized,
            PositionSizingRejectedEvent: cls._apply_rejected,
        }
