from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


@runtime_checkable
class OutboxRepository(Protocol):
    """
    Durable transactional outbox.

    Responsibilities:
    - Store recorded events in the same transaction as EventStore append.
    - Expose unpublished events to a separate relay process.
    - Mark events as published only after successful external publication.

    Critical invariant:
    - add() must be transaction-bound.
    - collect_unpublished() must be called outside the command transaction.
    """

    async def add(self, envelopes: Iterable[RecordedEventEnvelope]) -> None: ...

    async def collect_unpublished(
        self,
        *,
        limit: int,
    ) -> list[RecordedEventEnvelope]:
        """
        Retrieve a bounded batch of unpublished events.

        Must provide stable ordering.
        Should be implemented with locking/claiming in infrastructure
        to avoid duplicate workers publishing the same events concurrently.
        """
        ...

    async def mark_as_published(
        self,
        envelopes: Iterable[RecordedEventEnvelope],
    ) -> None:
        """
        Mark events as published after successful external publication.
        """
        ...
