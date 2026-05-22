from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
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
from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.errors.position_errors import PositionAlreadyClosed
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef
from quantum.domain.trading.position.events.position_closed_event import (
    PositionClosedEvent,
)
from quantum.domain.trading.position.events.position_opened_event import (
    PositionOpenedEvent,
)
from quantum.domain.trading.position.pnl_service import PnLService
from quantum.domain.trading.position.states.position_closed_state import (
    PositionClosedState,
)
from quantum.domain.trading.position.states.position_opened_state import (
    PositionOpenedState,
)
from quantum.domain.trading.position.states.position_state_base import PositionStateBase
from quantum.domain.trading.position.states.position_uninitialized_state import (
    PositionUninitializedState,
)


@dataclass(frozen=True, slots=True)
class PositionId(AggregateId):
    """Identity of the Order aggregate (event stream id)."""

    pass


class Position(EventSourcedAggregateRoot[PositionId, PositionStateBase]):
    """
    Event-sourced Position aggregate.
    """

    __slots__ = ()

    @classmethod
    def aggregate_id_type(cls) -> type[PositionId]:
        return PositionId

    @classmethod
    def state_type(cls) -> type[PositionStateBase]:
        return PositionStateBase

    @classmethod
    def uninitialized_state(cls) -> PositionStateBase:
        return PositionUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def open(
        *,
        broker_position_ref: BrokerPositionRef,
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
                broker_position_ref=broker_position_ref,
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
        instrument: InstrumentSpec,
    ) -> list[BaseEvent]:
        """
        Answers the question:
            "Do we have the right to close this position at this time,
            and if so, what must be recorded in the event stream?"

        This method represents a DOMAIN COMMAND.
        """

        state = self.state

        if isinstance(state, PositionClosedState):
            raise PositionAlreadyClosed("Position already closed")

        if not isinstance(state, PositionOpenedState):
            raise InvalidStateTransition("Position not opened")

        pnl = PnLService.compute_realized_pnl(
            entry_price=state.entry_price,
            exit_price=exit_price,
            volume=state.volume,
            side=state.side,
            instrument=instrument,
        )

        return [
            PositionClosedEvent(
                broker_position_ref=state.broker_position_ref,
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
            broker_position_ref=event.broker_position_ref,
            side=event.side,
            volume=event.volume,
            entry_price=event.entry_price,
        )

    @staticmethod
    def _apply_closed(
        state: PositionStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> PositionStateBase:
        """
        Applies PositionClosedEvent to an opened position.

        This transition is intentionally defensive:
        the persisted event must be compatible with the current aggregate state.
        """

        if isinstance(state, PositionClosedState):
            raise InvariantViolation("Position already closed")

        if not isinstance(state, PositionOpenedState):
            raise InvariantViolation("Position not opened")

        if not isinstance(event, PositionClosedEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_position_ref != state.broker_position_ref:
            raise InvariantViolation(
                "Illegal close event: broker_position_ref mismatch"
            )

        if event.side != state.side:
            raise InvariantViolation("Illegal close event: side mismatch")

        if event.volume != state.volume:
            raise InvariantViolation("Illegal close event: volume mismatch")

        return PositionClosedState(
            last_sequence=envelope.sequence,
            broker_position_ref=state.broker_position_ref,
            side=state.side,
            volume=state.volume,
            entry_price=state.entry_price,
            exit_price=event.exit_price,
            realized_pnl=event.realized_pnl,
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
