from collections.abc import Mapping

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
from quantum.domain.shared_kernel.modeling.monetary.money_context import MoneyContext
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.errors.position_errors import PositionAlreadyClosed
from quantum.domain.trading.execution.position.events.position_closed_event import (
    PositionClosedEvent,
)
from quantum.domain.trading.execution.position.events.position_opened_event import (
    PositionOpenedEvent,
)
from quantum.domain.trading.execution.position.pnl_service import PnLService
from quantum.domain.trading.execution.position.states.position_opened_state import (
    PositionOpenedState,
)
from quantum.domain.trading.execution.position.states.position_state_base import (
    PositionStateBase,
)
from quantum.domain.trading.execution.position.states.position_uninitialized_state import (
    PositionUninitializedState,
)
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.volume import PositiveVolume


class Position(EventSourcedAggregateRoot[PositionStateBase]):
    """
    Event-sourced Position aggregate.
    """

    __slots__ = ()

    @classmethod
    def uninitialized_state(cls) -> PositionStateBase:
        return PositionUninitializedState(
            last_sequence=EventSequence.initial(),
        )

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
            "Do we have the right to open a position,
            and if so, what must be recorded in the event stream?"

        This method represents a DOMAIN COMMAND.
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
            "Do we have the right to close this position at this time,
            and if so, what must be recorded in the event stream?"

        This method represents a DOMAIN COMMAND.
        """

        state = self.state

        if not isinstance(state, PositionOpenedState):
            raise InvalidStateTransition("Position not opened")

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
        state: PositionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> PositionStateBase:
        """
        Answers the question:
            "Given that this event has occurred, what is the new aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if not isinstance(state, PositionUninitializedState):
            raise InvariantViolation("Position already opened")

        if not isinstance(event, PositionOpenedEvent):
            raise InvariantViolation("Invalid event type")

        return PositionOpenedState(
            last_sequence=envelope.sequence,
            position_id=event.position_id,
            side=event.side,
            volume=event.volume,
            entry_price=event.entry_price,
            closed=False,
        )

    @staticmethod
    def _apply_closed(
        state: PositionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> PositionStateBase:
        """
        Answers the question:
            "Given that this event has occurred, what is the new aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if not isinstance(state, PositionOpenedState):
            raise InvariantViolation("Position not opened")

        if not isinstance(event, PositionClosedEvent):
            raise InvariantViolation("Invalid event type")

        if state.closed:
            raise InvariantViolation("Position already closed")

        return PositionOpenedState(
            last_sequence=envelope.sequence,
            position_id=state.position_id,
            side=state.side,
            volume=state.volume,
            entry_price=state.entry_price,
            closed=True,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[PositionStateBase, BaseEvent]]:
        return {
            PositionOpenedEvent: cls._apply_opened,
            PositionClosedEvent: cls._apply_closed,
        }
