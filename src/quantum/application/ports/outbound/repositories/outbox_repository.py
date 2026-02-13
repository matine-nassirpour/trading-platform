from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


@runtime_checkable
class OutboxRepository(Protocol):
    """
    Stores events inside the same transaction as the EventStore.
    """

    @abstractmethod
    def add(self, events: Iterable[EventEnvelope]) -> None:
        """
        Store events to be published after commit.
        Must be transaction-bound.
        """
        raise NotImplementedError

    @abstractmethod
    def collect_unpublished(self) -> list[EventEnvelope]:
        """
        Retrieve unpublished events (post-commit).
        """
        raise NotImplementedError

    @abstractmethod
    def mark_as_published(self, events: Iterable[EventEnvelope]) -> None:
        raise NotImplementedError
