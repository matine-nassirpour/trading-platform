from __future__ import annotations

from dataclasses import dataclass, field

from quantum.domain.events.base import BaseEvent


@dataclass(frozen=True)
class AggregateRoot:
    """
    Aggregate Root with domain event support.
    """

    _events: tuple[BaseEvent, ...] = field(default_factory=tuple, init=False)

    def _raise(self, event: BaseEvent):
        return self.__class__(
            **{
                **self.__dict__,
                "_events": self._events + (event,),
            }
        )

    @property
    def events(self) -> tuple[BaseEvent, ...]:
        return self._events
