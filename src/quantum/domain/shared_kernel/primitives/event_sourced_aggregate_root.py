from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, ClassVar, Self

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.primitives.aggregate_state import _AggregateState
from quantum.domain.shared_kernel.primitives.mutable_aggregate_root import (
    MutableAggregateRoot,
)
from quantum.domain.shared_kernel.primitives.validatable_aggregate import (
    ValidatableAggregate,
)

EventKey = tuple[str, int]  # (event_name, event_version)
EventHandler = Callable[[Any, BaseEvent], None]


class EventSourcedAggregateRoot(
    MutableAggregateRoot,
    ValidatableAggregate,
    DomainObject,
):
    """
    Canonical base class for all Event-Sourced Aggregates.

    HARD GUARANTEES:
    - Only BaseEvent instances may ever be applied
    - All state changes happen via domain events
    - No direct mutation is allowed
    - Aggregate invariants are validated after every event
    - Replay is fully deterministic
    - Event handlers are isolated per Aggregate class
    """

    __slots__ = ("_state", "_uncommitted_events")

    _EVENT_HANDLERS: ClassVar[dict[EventKey, EventHandler]]

    # --- Domain role ----------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.AGGREGATE

    # --- Class construction ---------------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Each Aggregate subclass gets its own handler registry
        cls._EVENT_HANDLERS = {}

    # --- Lifecycle ------------------------------------------------------------

    def __init__(self) -> None:
        object.__setattr__(self, "_state", _AggregateState())
        object.__setattr__(self, "_uncommitted_events", [])

    # --- Attribute access -----------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """
        All domain attributes are read from the protected state capsule.
        """
        state = object.__getattribute__(self, "_state")
        if name in state._data:
            return state.get(name)
        raise AttributeError(name)

    # --- Controlled mutation API (used only by engine) ------------------------

    def _mutate(self, name: str, value: Any) -> None:
        """
        Writes into the protected state capsule.
        This method is only callable while applying an event.
        """
        self._assert_mutating()
        self._state._set(name, value)

    # --- Event handling -------------------------------------------------------

    def _raise(self, event: BaseEvent) -> None:
        """
        Raises and applies a new domain event.
        """
        self._apply(event)
        self._validate_state()
        self._uncommitted_events.append(event)

    def _apply(self, event: BaseEvent) -> None:
        """
        Applies a single domain event inside a mutation-safe window.

        HARD GUARANTEE:
        - event MUST be a BaseEvent
        """

        if not isinstance(event, BaseEvent):
            raise InvariantViolation(
                f"{self.__class__.__name__} can only apply BaseEvent, "
                f"got {type(event).__name__}"
            )

        key = (event.event_name, event.event_version)

        handlers = self.__class__._EVENT_HANDLERS

        if key not in handlers:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot apply event {key}"
            )

        handler = handlers[key]

        self._begin_mutation()
        try:
            handler(self, event)
        finally:
            self._end_mutation()

    # --- Replay ---------------------------------------------------------------

    @classmethod
    def rehydrate(cls, events: Iterable[BaseEvent]) -> Self:
        """
        Rebuilds an aggregate from its event stream.
        """
        instance = cls.__new__(cls)
        EventSourcedAggregateRoot.__init__(instance)

        for event in events:
            instance._apply(event)

        instance._validate_state()
        return instance

    # --- Contracts ------------------------------------------------------------

    def _validate_state(self) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _validate_state()"
        )

    # --- Introspection --------------------------------------------------------

    def pull_uncommitted_events(self) -> tuple[BaseEvent, ...]:
        events = tuple(self._uncommitted_events)
        self._uncommitted_events.clear()
        return events
