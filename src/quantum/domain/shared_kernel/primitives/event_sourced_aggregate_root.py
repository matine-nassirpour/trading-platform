from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar, Final, Generic, Protocol, Self, TypeVar, cast

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.identifiers.aggregate_id import AggregateId
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState

S = TypeVar("S", bound=AggregateState)
ID = TypeVar("ID", bound=AggregateId)
E = TypeVar("E", bound=BaseEvent, contravariant=True)


class EventHandler(Protocol[S, E]):
    """
    Pure transition function:
        (state, event, envelope) -> new_state
    """

    def __call__(self, state: S, event: E, envelope: RecordedEventEnvelope) -> S: ...


@dataclass(frozen=True, slots=True)
class EventSourcedAggregateRoot(Generic[ID, S], ABC):
    """
    Canonical base class for Event-Sourced Aggregates.

    Guarantees:
    - Immutability
    - Deterministic replay
    - Strict sequence continuity
    - Event identity integrity
    - Aggregate identity protection
    - No hidden mutation

    Doctrine:
    - Aggregate identity is owned EXCLUSIVELY by the root.
    - Aggregate state is identity-free.
    """

    _aggregate_id: Final[ID]
    _state: Final[S]

    _HANDLERS_CACHE: ClassVar[dict[type, Mapping[type[BaseEvent], EventHandler]]] = {}

    def __post_init__(self) -> None:
        expected_id_type = self.aggregate_id_type()
        expected_state_type = self.state_type()

        if not isinstance(self._aggregate_id, expected_id_type):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires aggregate_id of type "
                f"{expected_id_type.__name__}, got {type(self._aggregate_id).__name__}"
            )

        if not isinstance(self._state, expected_state_type):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires state of type "
                f"{expected_state_type.__name__}, got {type(self._state).__name__}"
            )

    # --- Identity / state contract --------------------------------------------

    @classmethod
    @abstractmethod
    def aggregate_id_type(cls) -> type[ID]:
        """
        Returns the canonical AggregateId subtype for this aggregate.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def state_type(cls) -> type[S]:
        """
        Returns the canonical AggregateState subtype for this aggregate.
        """
        raise NotImplementedError

    @classmethod
    def _validate_aggregate_id(cls, aggregate_id: AggregateId) -> ID:
        expected_id_type = cls.aggregate_id_type()

        if not isinstance(aggregate_id, expected_id_type):
            raise InvariantViolation(
                f"{cls.__name__} requires aggregate_id of type "
                f"{expected_id_type.__name__}, got {type(aggregate_id).__name__}"
            )

        return cast(ID, aggregate_id)

    @classmethod
    def _validate_state(cls, state: AggregateState) -> S:
        expected_state_type = cls.state_type()

        if not isinstance(state, expected_state_type):
            raise InvariantViolation(
                f"{cls.__name__} requires state of type "
                f"{expected_state_type.__name__}, got {type(state).__name__}"
            )

        return cast(S, state)

    # --- Properties -----------------------------------------------------------

    @property
    def aggregate_id(self) -> ID:
        """
        Root-owned identity. Must be available even for uninitialized state.
        """
        return self._aggregate_id

    @property
    def state(self) -> S:
        """
        Returns immutable aggregate state.
        """
        return self._state

    @property
    def version(self) -> EventSequence:
        """
        Returns aggregate version.

        Version == last applied sequence.
        """
        return self.state.last_event_sequence()

    # --- Canonical initial state ----------------------------------------------

    @classmethod
    @abstractmethod
    def uninitialized_state(cls) -> S:
        """
        Canonical deterministic initial state.

        MUST:
        - Be pure
        - Be deterministic
        - Have EventSequence.initial()
        """
        raise NotImplementedError

    @classmethod
    def new(cls, *, aggregate_id: ID) -> Self:
        """
        Canonical constructor for a brand-new, empty aggregate.

        This is the ONLY supported way to obtain an uninitialized aggregate
        instance suitable for creation workflows.
        """
        validated_id = cls._validate_aggregate_id(aggregate_id)
        state = cls._validate_state(cls.uninitialized_state())

        if not state.last_event_sequence().is_initial():
            raise InvariantViolation(
                f"{cls.__name__}.uninitialized_state() must have initial sequence"
            )

        return cls(_aggregate_id=validated_id, _state=state)

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
        Returns immutable handler mapping, cached per aggregate class.
        """
        cached = cls._HANDLERS_CACHE.get(cls)
        if cached is not None:
            return cast(Mapping[type[BaseEvent], EventHandler[S, BaseEvent]], cached)

        handlers = cls._handlers()

        if not isinstance(handlers, Mapping):
            raise InvariantViolation(f"{cls.__name__}._handlers() must return Mapping")

        frozen_handlers = MappingProxyType(dict(handlers))
        cls._HANDLERS_CACHE[cls] = frozen_handlers

        return cast(
            Mapping[type[BaseEvent], EventHandler[S, BaseEvent]], frozen_handlers
        )

    # --- Single-event application (the ONLY semantic gate) --------------------

    def apply(self, envelope: RecordedEventEnvelope) -> Self:
        """
        Applies ONE persisted event.

        This is the ONLY legal state transition gateway.
        """

        if not isinstance(envelope, RecordedEventEnvelope):
            raise InvariantViolation("apply() requires RecordedEventEnvelope")

        if envelope.aggregate_id != self.aggregate_id:
            raise InvariantViolation("Event aggregate_id mismatch")

        event = envelope.event
        handler = self.handlers().get(type(event))

        if handler is None:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot handle event type "
                f"{type(event).__name__}"
            )

        previous_sequence = self.state.last_event_sequence()
        envelope.sequence.assert_is_next_of(previous_sequence)

        new_state = self._validate_state(handler(self.state, event, envelope))

        if new_state.last_event_sequence() != envelope.sequence:
            raise InvariantViolation(
                "Handler must advance sequence to envelope.sequence"
            )

        return self.__class__(_aggregate_id=self._aggregate_id, _state=new_state)

    # --- Replay (strictly defined in terms of apply) --------------------------

    @classmethod
    def _validate_rehydrate_input(
        cls,
        *,
        events: list[RecordedEventEnvelope],
        aggregate_id: ID | None,
    ) -> ID:
        if len(events) == 0:
            raise InvariantViolation(
                f"{cls.__name__}.rehydrate() requires at least one recorded event"
            )

        for i in range(1, len(events)):
            if events[i].sequence.value <= events[i - 1].sequence.value:
                raise InvariantViolation(
                    "Event stream is not strictly ordered by sequence"
                )

        stream_id = cls._validate_aggregate_id(events[0].aggregate_id)

        if aggregate_id is not None:
            validated_requested_id = cls._validate_aggregate_id(aggregate_id)

            if validated_requested_id != stream_id:
                raise InvariantViolation(
                    "aggregate_id parameter mismatch with stream aggregate_id"
                )

        return stream_id

    @classmethod
    def rehydrate(
        cls,
        *,
        events: Iterable[RecordedEventEnvelope],
        aggregate_id: ID | None = None,
    ) -> Self:
        """
        Deterministic rebuild from a persisted event stream.

        STRICT SEMANTICS:
        - rehydrate() is ONLY valid for an existing aggregate
        - the event stream MUST contain at least one recorded event
        """
        if events is None:
            raise InvariantViolation("events cannot be None")

        materialized = list(events)

        expected_id = cls._validate_rehydrate_input(
            events=materialized,
            aggregate_id=aggregate_id,
        )

        aggregate = cls.new(aggregate_id=expected_id)
        seen_event_ids: set[EventId] = set()

        for envelope in materialized:
            if envelope.aggregate_id != expected_id:
                raise InvariantViolation("Mixed aggregate stream")

            if envelope.id in seen_event_ids:
                raise InvariantViolation(f"Duplicate EventId detected: {envelope.id}")

            seen_event_ids.add(envelope.id)
            aggregate = aggregate.apply(envelope)

        return aggregate
