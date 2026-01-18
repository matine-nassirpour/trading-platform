from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Generic, Protocol, TypeVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState

S = TypeVar("S", bound=AggregateState)
E = TypeVar("E", bound=BaseEvent, contravariant=True)


class EventHandler(Protocol[S, E]):
    """
    Strongly-typed event handler contract.

    A handler:
    - receives a state
    - receives a concrete domain event
    - receives its envelope
    - returns a NEW state
    """

    def __call__(self, state: S, event: E, envelope: EventEnvelope) -> S: ...


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

    # --- Required contract ----------------------------------------------------

    @classmethod
    @abstractmethod
    def _handlers(cls) -> Mapping[type[BaseEvent], EventHandler[S, BaseEvent]]:
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
        handlers = self._handlers()

        handler = handlers.get(type(event))
        if handler is None:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot handle event {type(event).__name__}"
            )

        # --- Enforce sequence continuity
        previous = self._state.last_event_sequence()
        envelope.sequence.assert_is_next_of(previous)

        # --- Apply event
        new_state = handler(self._state, event, envelope)

        if not isinstance(new_state, AggregateState):
            raise InvariantViolation("Event handler must return an AggregateState")

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

        aggregate = cls(empty_state)

        for event in events:
            aggregate = aggregate.apply(event)

        return aggregate
