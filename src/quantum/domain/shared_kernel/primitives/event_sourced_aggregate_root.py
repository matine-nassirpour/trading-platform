# domain/shared_kernel/primitives/event_sourced_aggregate_root.py

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent

T = TypeVar("T", bound="EventSourcedAggregateRoot")


class EventSourcedAggregateRoot:
    """
    Base class for event-sourced aggregates.

    Rules:
    - State is derived exclusively from events
    - Aggregates NEVER mutate state directly
    - Events are applied via _apply(event)
    """

    def __init__(self) -> None:
        self._uncommitted_events: list[BaseEvent] = []

    # --- Event handling -------------------------------------------------------

    def _raise(self: T, event: BaseEvent) -> T:
        """
        Raises and applies a new domain event.
        """
        self._apply(event)
        self._uncommitted_events.append(event)
        return self

    def _apply(self, event: BaseEvent) -> None:
        """
        Dispatch event to the corresponding apply_<EventName> handler.
        """
        handler_name = f"_apply_{event.__class__.__name__}"
        handler = getattr(self, handler_name, None)

        if handler is None:
            raise RuntimeError(
                f"{self.__class__.__name__} cannot apply event {event.__class__.__name__}"
            )

        handler(event)

    # --- Replay ---------------------------------------------------------------

    @classmethod
    def rehydrate(cls: type[T], events: Iterable[BaseEvent]) -> T:
        """
        Reconstructs aggregate state from a stream of past events.
        """
        instance = cls.__new__(cls)
        EventSourcedAggregateRoot.__init__(instance)

        for event in events:
            instance._apply(event)

        return instance

    # --- Event access ---------------------------------------------------------

    @property
    def uncommitted_events(self) -> list[BaseEvent]:
        return list(self._uncommitted_events)

    def clear_uncommitted_events(self) -> None:
        self._uncommitted_events.clear()
