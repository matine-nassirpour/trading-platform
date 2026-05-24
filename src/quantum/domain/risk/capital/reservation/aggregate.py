from collections.abc import Mapping
from typing import Self

from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.capital.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.risk.capital.reservation.events.capital_consumed_event import (
    CapitalConsumedEvent,
)
from quantum.domain.risk.capital.reservation.events.capital_released_event import (
    CapitalReleasedEvent,
)
from quantum.domain.risk.capital.reservation.events.capital_reservation_rejected_event import (
    CapitalReservationRejectedEvent,
)
from quantum.domain.risk.capital.reservation.events.capital_reservation_requested_event import (
    CapitalReservationRequestedEvent,
)
from quantum.domain.risk.capital.reservation.events.capital_reserved_event import (
    CapitalReservedEvent,
)
from quantum.domain.risk.capital.reservation.reason_codes.capital_release_reason_code import (
    CapitalReleaseReasonCode,
)
from quantum.domain.risk.capital.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_consumed_state import (
    CapitalReservationConsumedState,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_pending_state import (
    CapitalReservationPendingState,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_rejected_state import (
    CapitalReservationRejectedState,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_released_state import (
    CapitalReservationReleasedState,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_reserved_state import (
    CapitalReservationReservedState,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_state_base import (
    CapitalReservationStateBase,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_uninitialized_state import (
    CapitalReservationUninitializedState,
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
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


class CapitalReservation(
    EventSourcedAggregateRoot[CapitalReservationId, CapitalReservationStateBase]
):
    """
    CapitalReservation — Risk Aggregate (PURE DOMAIN)

    Responsibilities:
    - represent a capital reservation request lifecycle
    - maintain reservation decision outcome
    - track reserved / released / consumed capital commitment state
    - provide a dedicated audit stream for risk capital commitment

    Explicitly DOES NOT:
    - evaluate trading intent governance
    - create orders
    - know about execution pricing
    - own the TradingIntent aggregate
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[CapitalReservationId]:
        return CapitalReservationId

    @classmethod
    def state_type(cls) -> type[CapitalReservationStateBase]:
        return CapitalReservationStateBase

    @classmethod
    def uninitialized_state(cls) -> CapitalReservationStateBase:
        return CapitalReservationUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Internal helpers -----------------------------------------------------

    @staticmethod
    def _assert_event_matches_stream_identity(
        *,
        event_reservation_id: CapitalReservationId,
        envelope: RecordedEventEnvelope,
    ) -> None:
        if event_reservation_id != envelope.aggregate_id:
            raise InvariantViolation(
                "Event reservation_id does not match envelope aggregate_id"
            )

    def _require_pending(self) -> CapitalReservationPendingState:
        state = self.state

        if isinstance(state, CapitalReservationUninitializedState):
            raise InvalidStateTransition("CapitalReservation not initialized")

        if isinstance(
            state,
            (
                CapitalReservationReservedState,
                CapitalReservationRejectedState,
                CapitalReservationReleasedState,
                CapitalReservationConsumedState,
            ),
        ):
            raise InvalidStateTransition("CapitalReservation is no longer pending")

        if not isinstance(state, CapitalReservationPendingState):
            raise InvariantViolation("Corrupted CapitalReservation state")

        return state

    def _require_reserved(self) -> CapitalReservationReservedState:
        state = self.state

        if isinstance(state, CapitalReservationUninitializedState):
            raise InvalidStateTransition("CapitalReservation not initialized")

        if isinstance(state, CapitalReservationPendingState):
            raise InvalidStateTransition("CapitalReservation has not been reserved yet")

        if isinstance(
            state,
            (
                CapitalReservationRejectedState,
                CapitalReservationReleasedState,
                CapitalReservationConsumedState,
            ),
        ):
            raise InvalidStateTransition(
                "CapitalReservation is no longer in reserved state"
            )

        if not isinstance(state, CapitalReservationReservedState):
            raise InvariantViolation("Corrupted CapitalReservation state")

        return state

    # --- Creation API ---------------------------------------------------------

    @classmethod
    def decide_request(
        cls,
        *,
        reservation_id: CapitalReservationId,
        decision_id: DecisionId,
        strategy_id: StrategyId,
        requested_allocation: CapitalAllocationIntent,
    ) -> list[BaseEvent]:
        """
        Pure domain decision for requesting a new capital reservation.
        """

        return [
            CapitalReservationRequestedEvent(
                reservation_id=reservation_id,
                decision_id=decision_id,
                strategy_id=strategy_id,
                requested_allocation=requested_allocation,
            )
        ]

    @classmethod
    def create_new(
        cls,
        *,
        aggregate_id: CapitalReservationId,
        decision_id: DecisionId,
        strategy_id: StrategyId,
        requested_allocation: CapitalAllocationIntent,
    ) -> tuple[Self, list[BaseEvent]]:
        """
        Canonical factory for a brand-new CapitalReservation aggregate.

        The returned aggregate intentionally remains EMPTY until the recorded
        creation envelope is persisted and applied.
        """

        aggregate = cls.new(aggregate_id=aggregate_id)

        domain_events = cls.decide_request(
            reservation_id=aggregate.aggregate_id,
            decision_id=decision_id,
            strategy_id=strategy_id,
            requested_allocation=requested_allocation,
        )

        return aggregate, domain_events

    # --- Commands -------------------------------------------------------------

    def reserve(
        self,
        *,
        reserved_allocation: CapitalAllocationIntent,
    ) -> list[BaseEvent]:
        """
        Accepts the reservation request and commits capital.

        The approved reservation MAY differ from the originally requested one.
        """

        state = self._require_pending()

        return [
            CapitalReservedEvent(
                reservation_id=self.aggregate_id,
                decision_id=state.decision_id,
                strategy_id=state.strategy_id,
                reserved_allocation=reserved_allocation,
            )
        ]

    def reject(
        self,
        *,
        reason_code: CapitalReservationRejectionReasonCode,
    ) -> list[BaseEvent]:
        """
        Rejects a pending reservation request.
        """

        state = self._require_pending()

        return [
            CapitalReservationRejectedEvent(
                reservation_id=self.aggregate_id,
                decision_id=state.decision_id,
                strategy_id=state.strategy_id,
                reason_code=reason_code,
            )
        ]

    def release(
        self,
        *,
        reason_code: CapitalReleaseReasonCode,
    ) -> list[BaseEvent]:
        """
        Releases previously reserved capital.
        """

        state = self._require_reserved()

        return [
            CapitalReleasedEvent(
                reservation_id=self.aggregate_id,
                decision_id=state.decision_id,
                strategy_id=state.strategy_id,
                reason_code=reason_code,
            )
        ]

    def consume(self) -> list[BaseEvent]:
        """
        Marks previously reserved capital as consumed by downstream execution.
        """

        state = self._require_reserved()

        return [
            CapitalConsumedEvent(
                reservation_id=self.aggregate_id,
                decision_id=state.decision_id,
                strategy_id=state.strategy_id,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_requested(
        state: CapitalReservationStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> CapitalReservationStateBase:
        if not isinstance(state, CapitalReservationUninitializedState):
            raise InvariantViolation("CapitalReservation already exists")

        if not isinstance(event, CapitalReservationRequestedEvent):
            raise InvariantViolation(
                "CapitalReservation._apply_requested requires "
                "CapitalReservationRequestedEvent"
            )

        CapitalReservation._assert_event_matches_stream_identity(
            event_reservation_id=event.reservation_id,
            envelope=envelope,
        )

        return CapitalReservationPendingState(
            last_sequence=envelope.sequence,
            decision_id=event.decision_id,
            strategy_id=event.strategy_id,
            requested_allocation=event.requested_allocation,
            requested_at=envelope.occurred_at,
        )

    @staticmethod
    def _apply_reserved(
        state: CapitalReservationStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> CapitalReservationStateBase:
        if not isinstance(state, CapitalReservationPendingState):
            raise InvariantViolation("CapitalReservation is not pending")

        if not isinstance(event, CapitalReservedEvent):
            raise InvariantViolation(
                "CapitalReservation._apply_reserved requires CapitalReservedEvent"
            )

        CapitalReservation._assert_event_matches_stream_identity(
            event_reservation_id=event.reservation_id,
            envelope=envelope,
        )

        if event.decision_id != state.decision_id:
            raise InvariantViolation(
                "CapitalReservedEvent.decision_id does not match reservation decision_id"
            )

        if event.strategy_id != state.strategy_id:
            raise InvariantViolation(
                "CapitalReservedEvent.strategy_id does not match reservation strategy_id"
            )

        return CapitalReservationReservedState(
            last_sequence=envelope.sequence,
            decision_id=state.decision_id,
            strategy_id=state.strategy_id,
            requested_allocation=state.requested_allocation,
            requested_at=state.requested_at,
            reserved_allocation=event.reserved_allocation,
            reserved_at=envelope.occurred_at,
        )

    @staticmethod
    def _apply_rejected(
        state: CapitalReservationStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> CapitalReservationStateBase:
        if not isinstance(state, CapitalReservationPendingState):
            raise InvariantViolation("CapitalReservation is not pending")

        if not isinstance(event, CapitalReservationRejectedEvent):
            raise InvariantViolation(
                "CapitalReservation._apply_rejected requires "
                "CapitalReservationRejectedEvent"
            )

        CapitalReservation._assert_event_matches_stream_identity(
            event_reservation_id=event.reservation_id,
            envelope=envelope,
        )

        if event.decision_id != state.decision_id:
            raise InvariantViolation(
                "CapitalReservationRejectedEvent.decision_id does not match "
                "reservation decision_id"
            )

        if event.strategy_id != state.strategy_id:
            raise InvariantViolation(
                "CapitalReservationRejectedEvent.strategy_id does not match "
                "reservation strategy_id"
            )

        return CapitalReservationRejectedState(
            last_sequence=envelope.sequence,
            decision_id=state.decision_id,
            strategy_id=state.strategy_id,
            requested_allocation=state.requested_allocation,
            requested_at=state.requested_at,
            rejection_reason_code=event.reason_code,
            rejected_at=envelope.occurred_at,
        )

    @staticmethod
    def _apply_released(
        state: CapitalReservationStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> CapitalReservationStateBase:
        if not isinstance(state, CapitalReservationReservedState):
            raise InvariantViolation("CapitalReservation is not reserved")

        if not isinstance(event, CapitalReleasedEvent):
            raise InvariantViolation(
                "CapitalReservation._apply_released requires CapitalReleasedEvent"
            )

        CapitalReservation._assert_event_matches_stream_identity(
            event_reservation_id=event.reservation_id,
            envelope=envelope,
        )

        if event.decision_id != state.decision_id:
            raise InvariantViolation(
                "CapitalReleasedEvent.decision_id does not match reservation decision_id"
            )

        if event.strategy_id != state.strategy_id:
            raise InvariantViolation(
                "CapitalReleasedEvent.strategy_id does not match reservation strategy_id"
            )

        return CapitalReservationReleasedState(
            last_sequence=envelope.sequence,
            decision_id=state.decision_id,
            strategy_id=state.strategy_id,
            requested_allocation=state.requested_allocation,
            requested_at=state.requested_at,
            reserved_allocation=state.reserved_allocation,
            reserved_at=state.reserved_at,
            release_reason_code=event.reason_code,
            released_at=envelope.occurred_at,
        )

    @staticmethod
    def _apply_consumed(
        state: CapitalReservationStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> CapitalReservationStateBase:
        if not isinstance(state, CapitalReservationReservedState):
            raise InvariantViolation("CapitalReservation is not reserved")

        if not isinstance(event, CapitalConsumedEvent):
            raise InvariantViolation(
                "CapitalReservation._apply_consumed requires CapitalConsumedEvent"
            )

        CapitalReservation._assert_event_matches_stream_identity(
            event_reservation_id=event.reservation_id,
            envelope=envelope,
        )

        if event.decision_id != state.decision_id:
            raise InvariantViolation(
                "CapitalConsumedEvent.decision_id does not match reservation decision_id"
            )

        if event.strategy_id != state.strategy_id:
            raise InvariantViolation(
                "CapitalConsumedEvent.strategy_id does not match reservation strategy_id"
            )

        return CapitalReservationConsumedState(
            last_sequence=envelope.sequence,
            decision_id=state.decision_id,
            strategy_id=state.strategy_id,
            requested_allocation=state.requested_allocation,
            requested_at=state.requested_at,
            reserved_allocation=state.reserved_allocation,
            reserved_at=state.reserved_at,
            consumed_at=envelope.occurred_at,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[CapitalReservationStateBase, BaseEvent]]:
        return {
            CapitalReservationRequestedEvent: cls._apply_requested,
            CapitalReservedEvent: cls._apply_reserved,
            CapitalReservationRejectedEvent: cls._apply_rejected,
            CapitalReleasedEvent: cls._apply_released,
            CapitalConsumedEvent: cls._apply_consumed,
        }
