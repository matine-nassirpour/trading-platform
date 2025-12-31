from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import Self

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.events.base_event import BaseEvent


@dataclass(frozen=True)
class AggregateRoot(ABC):
    """
    Canonical Aggregate Root.

    Guarantees:
    - Immutability
    - Explicit invariant validation
    - Monotonic domain events
    """

    _events: tuple[BaseEvent, ...] = field(
        default_factory=tuple,
        repr=False,
        compare=False,
        kw_only=True,
    )

    def __post_init__(self) -> None:
        self._validate()
        self._validate_events()

    # --- Invariants -----------------------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        raise NotImplementedError

    def _validate_events(self) -> None:
        if not isinstance(self._events, tuple):
            raise InvariantViolation("Aggregate events must be stored as a tuple")

        for event in self._events:
            if not isinstance(event, BaseEvent):
                raise InvariantViolation("Invalid domain event attached to aggregate")

    # --- Domain Events --------------------------------------------------------

    def _raise(self: Self, event: BaseEvent) -> Self:
        """
        Returns a new aggregate instance with the event appended.
        """
        return replace(self, _events=self._events + (event,))

    @property
    def events(self) -> tuple[BaseEvent, ...]:
        return self._events
