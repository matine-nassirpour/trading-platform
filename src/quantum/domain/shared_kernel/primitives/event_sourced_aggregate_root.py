from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState

S = TypeVar("S", bound=AggregateState)
EventHandler = Callable[..., AggregateState]


class EventSourcedAggregateRoot(Generic[S], ABC):
    """
    Canonical base class for Event-Sourced Aggregates.

    Design:
    - Aggregates are immutable shells around an immutable state
    - Events are applied by producing a NEW state
    - No hidden mutation
    - Replay is pure and deterministic
    """

    _state: S

    def __init__(self, state: S) -> None:
        if not isinstance(state, AggregateState):
            raise InvariantViolation("state must be an AggregateState")

        self._state = state

    # --- State access ---------------------------------------------------------

    @property
    def state(self) -> S:
        return self._state

    # --- Event application ----------------------------------------------------

    @classmethod
    @abstractmethod
    def _handlers(cls) -> dict[type[BaseEvent], EventHandler]:
        """
        Returns the event → state transition map.

        Each handler must be pure:
            (state, event, envelope) → new_state
        """
        raise NotImplementedError

    # --- Single-event application (the ONLY semantic gate) --------------------

    def apply(self, envelope: EventEnvelope) -> EventSourcedAggregateRoot[S]:
        """
        Applies a single EventEnvelope to this aggregate.

        This method is the ONLY gateway through which an event may
        affect aggregate state.
        """

        if not isinstance(envelope, EventEnvelope):
            raise InvariantViolation("apply() requires an EventEnvelope")

        event = envelope.event

        if not isinstance(event, BaseEvent):
            raise InvariantViolation("EventEnvelope.event must be a BaseEvent")

        handlers = self._handlers()
        event_type = type(event)

        if event_type not in handlers:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot handle event {event_type.__name__}"
            )

        # --- Enforce event sequence continuity
        prev_seq = self._state.last_event_sequence()
        new_seq = envelope.sequence

        if not isinstance(prev_seq, EventSequence):
            raise InvariantViolation(
                "State.last_event_sequence() must return EventSequence"
            )

        if not isinstance(new_seq, EventSequence):
            raise InvariantViolation("Envelope.sequence must be an EventSequence")

        new_seq.assert_is_next_of(prev_seq)

        # --- Compute new state (pure function)
        new_state = handlers[event_type](self._state, event, envelope)

        if not isinstance(new_state, AggregateState):
            raise InvariantViolation("Event handler must return an AggregateState")

        # --- Construct new aggregate (AggregateState invariants are re-validated)
        return self.__class__(new_state)

    # --- Replay (strictly defined in terms of apply) --------------------------

    @classmethod
    def rehydrate(
        cls,
        *,
        events: Iterable[EventEnvelope],
        empty_state: S,
    ) -> EventSourcedAggregateRoot[S]:
        """
        Rebuilds an aggregate from its full event stream.

        HARD GUARANTEES:
        - Every event is validated via apply()
        - No bypass of domain invariants
        - Replay semantics == live semantics
        """

        if not isinstance(empty_state, AggregateState):
            raise InvariantViolation("empty_state must be an AggregateState")

        aggregate = cls(empty_state)

        for event in events:
            aggregate = aggregate.apply(event)

        return aggregate
