from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, ClassVar, Self

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.handler_registry import build_handler_registry
from quantum.domain.shared_kernel.primitives.aggregate_state import _AggregateState
from quantum.domain.shared_kernel.primitives.mutable_aggregate_root import (
    MutableAggregateRoot,
)
from quantum.domain.shared_kernel.primitives.validatable_aggregate import (
    ValidatableAggregate,
)

EventKey = tuple[str, int]  # (event_name, event_version)


class EventSourcedAggregateRoot(
    MutableAggregateRoot,
    ValidatableAggregate,
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

    __slots__ = ("_state",)

    _EVENT_HANDLERS: ClassVar[Mapping[EventKey, Callable]]

    # --- Domain role ----------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.AGGREGATE

    # --- Class construction ---------------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Compile and freeze the handler registry
        cls._EVENT_HANDLERS = build_handler_registry(cls)

    # --- Lifecycle ------------------------------------------------------------

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "_state", _AggregateState())

    # --- Attribute access -----------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        state = object.__getattribute__(self, "_state")
        if name in state._data:
            return state._data[name]
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

    def _raise(self, event: BaseEvent) -> BaseEvent:
        """
        Applies a new domain event and returns it.
        """
        self._apply(event)
        self._validate_state()
        return event

    def _apply(self, event: BaseEvent) -> None:
        """
        Applies a single domain event inside a mutation-safe window.
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

        with self._mutation_window():
            handler(self, event)

    # --- Replay ---------------------------------------------------------------

    @classmethod
    def rehydrate(cls, events: Iterable[BaseEvent]) -> Self:
        """
        Rebuilds an aggregate from its event stream.
        """
        instance = cls.__new__(cls)
        cls.__init__(instance)

        for event in events:
            instance._apply(event)

        instance._validate_state()
        return instance

    # --- Contracts ------------------------------------------------------------

    def _validate_state(self) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _validate_state()"
        )
