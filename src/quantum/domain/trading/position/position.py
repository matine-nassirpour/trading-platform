from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.errors.position_errors import PositionAlreadyClosed
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.events.v1.position_closed_event import PositionClosedEvent
from quantum.domain.trading.events.v1.position_opened_event import PositionOpenedEvent
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.position.pnl_service import PnLService
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


@dataclass(frozen=True, slots=True)
class PositionStateData(AggregateState):
    """
    Immutable, fully event-sourced Position state.
    """

    last_sequence: EventSequence

    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price

    closed: bool

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate(self) -> None:
        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation("last_sequence must be EventSequence")

        if not isinstance(self.position_id, PositionId):
            raise InvariantViolation("PositionId missing")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("PositionSide missing")

        if not isinstance(self.volume, PositiveVolume):
            raise InvariantViolation("Volume missing")

        if not isinstance(self.entry_price, Price):
            raise InvariantViolation("Entry price missing")

        if not isinstance(self.closed, bool):
            raise InvariantViolation("Closed flag must be boolean")


class Position(EventSourcedAggregateRoot[PositionStateData]):
    """
    Event-sourced Position aggregate.
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def open(
        *,
        position_id: PositionId,
        side: PositionSide,
        volume: PositiveVolume,
        entry_price: Price,
    ) -> list[BaseEvent]:
        """
        Answers the question:
        "Do we have the right to open a position, and if so, what must be recorded in the event stream?"

        This method represents a DOMAIN COMMAND.

        Responsibilities:
        - Evaluate all business rules required to open a position
        - Decide whether the operation is allowed
        - Produce the domain events that must be persisted if allowed

        Guarantees:
        - Does NOT mutate any aggregate state
        - Produces immutable domain events only
        - May refuse the operation by raising a domain error
        - May produce one or more events

        Important:
        - This method is NOT replayed
        - This method expresses intent, not fact
        """

        return [
            PositionOpenedEvent(
                position_id=position_id,
                side=side,
                volume=volume,
                entry_price=entry_price,
            )
        ]

    # --- Commands -------------------------------------------------------------

    def close(
        self,
        *,
        exit_price: Price,
        context: MoneyContext,
    ) -> list[BaseEvent]:
        """
        Answers the question:
        "Do we have the right to close this position at this time, and if so, what must be recorded in the event stream?"

        This method represents a DOMAIN COMMAND.

        Responsibilities:
        - Validate that the position can be closed
        - Compute the realized PnL in the given MoneyContext
        - Produce the domain events that must be persisted

        Guarantees:
        - Does NOT mutate aggregate state
        - Produces immutable domain events only
        - May refuse the operation by raising a domain error

        Important:
        - The PnL computation is contextual and MUST happen here
        - This method is NOT replayed
        """

        state = self.state

        if state.closed:
            raise PositionAlreadyClosed("Position already closed")

        pnl = PnLService.compute_realized_pnl(
            entry_price=state.entry_price,
            exit_price=exit_price,
            volume=state.volume,
            side=state.side,
            context=context,
        )

        return [
            PositionClosedEvent(
                position_id=state.position_id,
                side=state.side,
                volume=state.volume,
                exit_price=exit_price,
                realized_pnl=pnl,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_opened(
        state: PositionStateData | None,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> PositionStateData:
        """
        Answers the question:
        "Given that this event has occurred, what is the new aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.

        Responsibilities:
        - Construct the new immutable aggregate state
        - Enforce structural and aggregate invariants via construction

        Guarantees:
        - Pure and deterministic
        - Side-effect free
        - Replayable with identical results
        - Does NOT make any business decisions
        - Does NOT validate whether the event *should* have happened

        Important:
        - This method MUST NOT fail for valid historical events
        - This method is part of the causal model, not governance
        """

        if state is not None:
            raise InvariantViolation("Position already initialized")

        assert isinstance(event, PositionOpenedEvent)

        return PositionStateData(
            last_sequence=envelope.sequence,
            position_id=event.position_id,
            side=event.side,
            volume=event.volume,
            entry_price=event.entry_price,
            closed=False,
        )

    @staticmethod
    def _apply_closed(
        state: PositionStateData,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> PositionStateData:
        """
        Answers the question:
        "Given that this event has occurred, what is the new aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.

        Responsibilities:
        - Transition the aggregate into its closed state
        - Update the event sequence

        Guarantees:
        - Pure and deterministic
        - Side-effect free
        - Replayable
        - No business logic
        - No calculations

        Important:
        - All semantic meaning MUST already be captured in the event
        - This method only applies recorded facts
        """

        assert isinstance(event, PositionClosedEvent)

        return PositionStateData(
            last_sequence=envelope.sequence,
            position_id=state.position_id,
            side=state.side,
            volume=state.volume,
            entry_price=state.entry_price,
            closed=True,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[
        type[BaseEvent],
        EventHandler[PositionStateData, BaseEvent],
    ]:
        return {
            PositionOpenedEvent: cls._apply_opened,
            PositionClosedEvent: cls._apply_closed,
        }
