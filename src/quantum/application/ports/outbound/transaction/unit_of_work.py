from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from quantum.application.ports.outbound.transaction.unit_of_work_state import (
    UnitOfWorkState,
)


@runtime_checkable
class UnitOfWork(Protocol):
    """
    Explicit asynchronous transactional boundary.

    State machine:

        NEW
         │
         ▼
        ACTIVE
        ├── commit()   ──► COMMITTED ──► DISPOSED
        └── rollback() ──► ROLLED_BACK ─► DISPOSED

    Invariants:
    - __aenter__ begins the transaction.
    - commit() is valid only in ACTIVE.
    - rollback() is valid only in ACTIVE.
    - __aexit__ must rollback if still ACTIVE.
    - __aexit__ must dispose resources exactly once.
    - No post-commit callback is allowed inside UnitOfWork.
    """

    @property
    def state(self) -> UnitOfWorkState:
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
