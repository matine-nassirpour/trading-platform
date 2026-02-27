from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Generic, Protocol, Self, TypeVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.persisted_event_envelope import (
    PersistedEventEnvelope,
)
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState

S = TypeVar("S", bound=AggregateState)
E = TypeVar("E", bound=BaseEvent, contravariant=True)


class EventHandler(Protocol[S, E]):
    """
    Pure transition function:
        (state, event, envelope) -> new_state
    """

    def __call__(self, state: S, event: E, envelope: PersistedEventEnvelope) -> S: ...


@dataclass(frozen=True, slots=True)
class EventSourcedAggregateRoot(Generic[S], ABC):
    """
    Canonical base class for Event-Sourced Aggregates.

    Guarantees:
    - Immutability
    - Deterministic replay
    - Strict sequence continuity
    - Event identity integrity
    - Aggregate identity protection
    - Handler completeness enforcement
    - No hidden mutation
    """

    _state: Final[S]

    def __post_init__(self) -> None:
        if not isinstance(self._state, AggregateState):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires AggregateState"
            )

    @property
    def state(self) -> S:
        """
        Returns immutable aggregate state.
        """
        return self._state

    # --- Canonical empty state (must be defined by each aggregate) ------------

    @classmethod
    @abstractmethod
    def empty_state(cls) -> S:
        """
        Canonical deterministic initial state.

        MUST:
        - Be pure
        - Be deterministic
        - Have EventSequence.initial()
        """
        raise NotImplementedError

    # --- Required contract ----------------------------------------------------

    @classmethod
    @abstractmethod
    def _handlers(cls) -> Mapping[type[BaseEvent], EventHandler[S, BaseEvent]]:
        """
        Returns COMPLETE handler mapping.

        This mapping defines the aggregate vocabulary.

        MUST:
        - Be total
        - Be deterministic
        - Not change at runtime
        """
        raise NotImplementedError

    @classmethod
    def handlers(cls) -> Mapping[type[BaseEvent], EventHandler[S, BaseEvent]]:
        """
        Returns immutable handler mapping.

        No caching used to avoid polymorphic corruption risk.
        """

        handlers = cls._handlers()

        if not isinstance(handlers, Mapping):
            raise InvariantViolation(f"{cls.__name__}._handlers() must return Mapping")

        return MappingProxyType(dict(handlers))

    # --- Single-event application (the ONLY semantic gate) --------------------

    def apply(self, envelope: PersistedEventEnvelope) -> Self:
        """
        Applies ONE persisted event.

        This is the ONLY legal mutation gateway.
        """

        if not isinstance(envelope, PersistedEventEnvelope):
            raise InvariantViolation("apply() requires PersistedEventEnvelope")

        event = envelope.event
        handler = self.handlers().get(type(event))

        if handler is None:
            raise InvariantViolation(
                f"{self.__class__.__name__} "
                f"cannot handle event type {type(event).__name__}"
            )

        # --- Enforce sequence continuity
        previous_sequence = self.state.last_event_sequence()
        envelope.sequence.assert_is_next_of(previous_sequence)

        # --- Apply transition
        new_state = handler(self.state, event, envelope)

        if not isinstance(new_state, AggregateState):
            raise InvariantViolation("Event handler must return AggregateState")

        if new_state.last_event_sequence() != envelope.sequence:
            raise InvariantViolation(
                "Handler must advance sequence to envelope.sequence"
            )

        return self.__class__(new_state)

    # --- Replay (strictly defined in terms of apply) --------------------------

    @classmethod
    def rehydrate(cls, *, events: Iterable[PersistedEventEnvelope]) -> Self:
        """
        Deterministic rebuild from persisted event stream.

        Guarantees:

        - Sorted replay
        - Duplicate detection
        - Gap detection
        - Identity integrity
        """

        if events is None:
            raise InvariantViolation("events cannot be None")

        ordered = sorted(events, key=lambda e: e.sequence.value)

        aggregate = cls(cls.empty_state())

        last_sequence = aggregate.state.last_event_sequence()
        seen_event_ids: set[EventId] = set()

        for envelope in ordered:
            if envelope.id in seen_event_ids:
                raise InvariantViolation(f"Duplicate EventId detected: {envelope.id}")

            seen_event_ids.add(envelope.id)
            envelope.sequence.assert_is_next_of(last_sequence)
            aggregate = aggregate.apply(envelope)
            last_sequence = envelope.sequence

        return aggregate

    # --- Version --------------------------------------------------------------

    @property
    def version(self) -> EventSequence:
        """
        Returns aggregate version.

        Version == last applied sequence.
        """
        return self.state.last_event_sequence()
