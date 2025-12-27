from __future__ import annotations

from dataclasses import dataclass, field, replace

from quantum.domain.events.base import BaseEvent


@dataclass(frozen=True)
class AggregateRoot:
    """
    Canonical Aggregate Root with immutable domain event support.
    """

    _events: tuple[BaseEvent, ...] = field(
        default_factory=tuple,
        repr=False,
        compare=False,
        init=True,
        kw_only=True,
    )

    def _raise(self, event: BaseEvent):
        return replace(self, _events=self._events + (event,))

    @property
    def events(self) -> tuple[BaseEvent, ...]:
        return self._events
