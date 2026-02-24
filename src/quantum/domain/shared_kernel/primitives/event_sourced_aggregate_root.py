from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, Protocol, Self, TypeVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState

S = TypeVar("S", bound=AggregateState)
E = TypeVar("E", bound=BaseEvent, contravariant=True)


class EventHandler(Protocol[S, E]):
    """
    Pure transition function:
        (state, event, envelope) -> new_state
    """

    def __call__(self, state: S, event: E, envelope: EventEnvelope) -> S: ...


@dataclass(frozen=True, slots=True)
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

    def __post_init__(self) -> None:
        if not isinstance(self._state, AggregateState):
            raise InvariantViolation("Aggregate state must be an AggregateState")

    @property
    def state(self) -> S:
        return self._state

    # --- Canonical empty state (must be defined by each aggregate) ------------

    @classmethod
    @abstractmethod
    def empty_state(cls) -> S:
        """
        Returns the only allowed canonical initial state for this aggregate.
        Must be deterministic and side-effect free.
        """
        raise NotImplementedError

    # --- Required contract ----------------------------------------------------

    @classmethod
    @abstractmethod
    def _handlers(cls) -> Mapping[type[BaseEvent], EventHandler[S, BaseEvent]]:
        """
        Event type -> pure state transition handler.

        Must be total with respect to the aggregate's event vocabulary.
        """
        raise NotImplementedError

    @classmethod
    def handlers(cls) -> Mapping[type[BaseEvent], EventHandler[S, BaseEvent]]:
        """
        Returns an immutable view of handlers (prevents accidental mutation).
        """
        h = cls._handlers()
        if not isinstance(h, Mapping):
            raise InvariantViolation("_handlers() must return a Mapping")
        return MappingProxyType(dict(h))

    # --- Single-event application (the ONLY semantic gate) --------------------

    def apply(self, envelope: EventEnvelope) -> Self:
        """
        Applies a single EventEnvelope to this aggregate.

        This method is the ONLY gateway through which an event may
        affect aggregate state.
        """

        if not isinstance(envelope, EventEnvelope):
            raise InvariantViolation("apply() requires an EventEnvelope")

        event = envelope.event
        handler = self.handlers().get(type(event))
        if handler is None:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot handle event {type(event).__name__}"
            )

        # --- Enforce sequence continuity
        if envelope.sequence is None:
            raise InvariantViolation("EventEnvelope.sequence must be assigned")

        previous = self._state.last_event_sequence()
        envelope.sequence.assert_is_next_of(previous)

        # --- Apply event
        new_state = handler(self._state, event, envelope)

        if not isinstance(new_state, AggregateState):
            raise InvariantViolation("Event handler must return an AggregateState")

        if new_state.last_event_sequence() != envelope.sequence:
            raise InvariantViolation(
                "Handler must advance state sequence to envelope.sequence"
            )

        return self.__class__(new_state)

    # --- Replay (strictly defined in terms of apply) --------------------------

    @classmethod
    def rehydrate(cls, *, events: Iterable[EventEnvelope]) -> Self:
        """
        Canonical rebuild from stream.
        """

        aggregate: Self = cls(cls.empty_state())
        for event in events:
            aggregate = aggregate.apply(event)
        return aggregate
