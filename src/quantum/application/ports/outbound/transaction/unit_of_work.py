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
    def state(self) -> UnitOfWorkState:
        raise NotImplementedError

    @property
    def event_store(self) -> EventStore:
        """
        Transaction-bound EventStore.
        Must only be used while UnitOfWork is ACTIVE.
        """
        raise NotImplementedError

    @property
    def outbox(self) -> OutboxRepository:
        """
        Transaction-bound OutboxRepository.
        Must only be used while UnitOfWork is ACTIVE.
        """
        raise NotImplementedError

    @property
    def command_deduplication(self) -> CommandDeduplicationRepository:
        """
        Transaction-bound command deduplication repository.
        Must only be used while UnitOfWork is ACTIVE.
        """
        raise NotImplementedError

    async def __aenter__(self) -> Self:
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        raise NotImplementedError

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError
