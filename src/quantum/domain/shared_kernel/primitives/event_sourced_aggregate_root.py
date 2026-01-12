from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Self

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
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

    _is_applying_event: bool
    _uncommitted_events: list[BaseEvent]

    # --- Domain role ----------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.AGGREGATE

    # --- Lifecycle ------------------------------------------------------------

    def __init__(self) -> None:
        object.__setattr__(self, "_is_applying_event", False)
        object.__setattr__(self, "_uncommitted_events", [])

    # --- Mutation barrier -----------------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Forbids any mutation unless we are inside event application.
        """
        if not getattr(self, "_is_applying_event", False):
            raise InvariantViolation(
                f"Illegal mutation of aggregate {self.__class__.__name__}.{name}. "
                "State may only be changed while applying a domain event."
            )
        object.__setattr__(self, name, value)

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
        object.__setattr__(self, "_is_applying_event", True)
        try:
            self._apply(event)
        finally:
            object.__setattr__(self, "_is_applying_event", False)

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
