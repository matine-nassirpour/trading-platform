from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.validatable_aggregate import (
    ValidatableAggregate,
)

S = TypeVar("S", bound=AggregateState)


class EventSourcedAggregateRoot(Generic[S], ValidatableAggregate, ABC):
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
        self._state = state
        self._validate_state()

    # --- State access ---------------------------------------------------------

    @property
    def state(self) -> S:
        return self._state

    # --- Event application ----------------------------------------------------

    @classmethod
    @abstractmethod
    def _handlers(cls) -> dict[type[BaseEvent], Callable[[S, BaseEvent], S]]:
        """
        Returns the event → state transition map.

        Each handler must be pure:
        (state, event) → new_state
        """
        raise NotImplementedError

    def apply(self, event: BaseEvent) -> EventSourcedAggregateRoot[S]:
        if not isinstance(event, BaseEvent):
            raise InvariantViolation("Only BaseEvent can be applied")

        handlers = self._handlers()
        event_type = type(event)

        if event_type not in handlers:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot handle event {event_type.__name__}"
            )

        new_state = handlers[event_type](self._state, event)

        return self.__class__(new_state)

    # --- Replay ---------------------------------------------------------------

    @classmethod
    def rehydrate(cls, events: Iterable[BaseEvent], empty_state: S):
        state = empty_state
        for event in events:
            handlers = cls._handlers()
            handler = handlers.get(type(event))
            if handler is None:
                raise InvariantViolation(
                    f"{cls.__name__} cannot handle event {type(event).__name__}"
                )
            state = handler(state, event)

        return cls(state)
