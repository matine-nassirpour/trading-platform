from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from quantum.application.ports.outbound.transaction.command_deduplication_repository import (
    CommandDeduplicationRepository,
)
from quantum.application.ports.outbound.transaction.event_store import EventStore
from quantum.application.ports.outbound.transaction.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.transaction.unit_of_work_state import (
    UnitOfWorkState,
)


@runtime_checkable
class UnitOfWork(Protocol):
    """
    Explicit asynchronous transactional boundary.

    Critical invariant:
    - All repositories exposed by this UnitOfWork MUST be transaction-bound.
    - EventStore append and Outbox add MUST commit or rollback atomically.
    """

    @property
    def state(self) -> UnitOfWorkState: ...

    @property
    def event_store(self) -> EventStore:
        """
        Transaction-bound EventStore.
        Must only be used while UnitOfWork is ACTIVE.
        """
        ...

    @property
    def outbox(self) -> OutboxRepository:
        """
        Transaction-bound OutboxRepository.
        Must only be used while UnitOfWork is ACTIVE.
        """
        ...

    @property
    def command_deduplication(self) -> CommandDeduplicationRepository:
        """
        Transaction-bound command deduplication repository.
        Must only be used while UnitOfWork is ACTIVE.
        """
        ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
