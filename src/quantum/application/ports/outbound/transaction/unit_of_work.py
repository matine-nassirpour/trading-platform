from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable

from quantum.application.ports.outbound.transaction.unit_of_work_state import (
    UnitOfWorkState,
)


@runtime_checkable
class UnitOfWork(Protocol, AbstractContextManager["UnitOfWork"]):
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
    - commit() is valid only in ACTIVE.
    - rollback() is valid only in ACTIVE.
    - __exit__ must rollback if still ACTIVE.
    - __exit__ must dispose resources exactly once.
    - No post-commit callback is allowed inside UnitOfWork.
    """

    @property
    def state(self) -> UnitOfWorkState:
        raise NotImplementedError

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError
