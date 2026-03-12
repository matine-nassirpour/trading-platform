from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


@runtime_checkable
class OutboxRepository(Protocol):
    """
    Stores events inside the same transaction as the EventStore.
    """

    @abstractmethod
    def add(self, envelopes: Iterable[RecordedEventEnvelope]) -> None:
        """
        Store events to be published after commit.
        Must be transaction-bound.
        """
        raise NotImplementedError

    @abstractmethod
    def collect_unpublished(self) -> list[RecordedEventEnvelope]:
        """
        Retrieve unpublished events (post-commit).
        """
        raise NotImplementedError

    @abstractmethod
    def mark_as_published(self, envelopes: Iterable[RecordedEventEnvelope]) -> None:
        raise NotImplementedError
