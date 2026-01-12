from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Self

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.primitives.aggregate_state import _AggregateState
from quantum.domain.shared_kernel.primitives.validatable_aggregate import (
    ValidatableAggregate,
)


class EventSourcedAggregateRoot(ValidatableAggregate, DomainObject):
    """
    Canonical base class for all Event-Sourced aggregates.

    HARD RULES:
    - All state transitions happen via domain events
    - No direct mutation is allowed
    - Aggregate state MUST be valid after every event
    - Deterministic replay MUST always reconstruct a valid state
    - State is validated after every event
    """

    __slots__ = ("_state", "_uncommitted_events", "_is_applying")

    # --- Domain role ----------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.AGGREGATE

    # --- Lifecycle ------------------------------------------------------------

    def __init__(self) -> None:
        object.__setattr__(self, "_state", _AggregateState())
        object.__setattr__(self, "_uncommitted_events", [])
        object.__setattr__(self, "_is_applying", False)

    # --- Attribute access -----------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """
        All domain attributes are read from the protected state capsule.
        """
        state = object.__getattribute__(self, "_state")
        if name in state._data:
            return state.get(name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevent ANY direct mutation of the aggregate.
        """
        raise InvariantViolation(
            f"Direct mutation of Aggregate '{self.__class__.__name__}' is forbidden. "
            "All changes must occur through domain events."
        )

    # --- Controlled mutation API (used only by engine) ------------------------

    def _mutate(self, name: str, value: Any) -> None:
        """
        Writes into the protected state capsule.
        This method is only callable while applying an event.
        """
        if not self._is_applying:
            raise InvariantViolation("Aggregate mutation outside event application")
        self._state._set(name, value)

    # --- Event handling -------------------------------------------------------

    def _raise(self, event: BaseEvent) -> None:
        """
        Raises and applies a domain event.
        """
        self._apply_with_guard(event)
        self._validate_state()
        self._uncommitted_events.append(event)

    def _apply_with_guard(self, event: BaseEvent) -> None:
        """
        Applies an event inside a mutation-safe window.
        """
        object.__setattr__(self, "_is_applying", True)
        try:
            self._apply(event)
        finally:
            object.__setattr__(self, "_is_applying", False)

    def _apply(self, event: BaseEvent) -> None:
        """
        Dispatches event to the appropriate handler.
        """
        handler_name = f"_apply_{event.__class__.__name__.lower()}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot apply {event.__class__.__name__}"
            )
        handler(event)

    # --- Replay ---------------------------------------------------------------

    @classmethod
    def rehydrate(cls, events: Iterable[BaseEvent]) -> Self:
        """
        Rebuilds an aggregate from its event stream.
        """
        instance = cls.__new__(cls)
        EventSourcedAggregateRoot.__init__(instance)

        for event in events:
            instance._apply_with_guard(event)

        instance._validate_state()
        return instance

    # --- Contracts ------------------------------------------------------------

    def _validate_state(self) -> None:
        """
        Aggregate-wide invariant validation.

        MUST be overridden by concrete aggregates.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _validate_state()"
        )

    # --- Introspection --------------------------------------------------------

    def pull_uncommitted_events(self) -> tuple[BaseEvent, ...]:
        """
        Returns and clears uncommitted events.
        """
        events = tuple(self._uncommitted_events)
        self._uncommitted_events.clear()
        return events
