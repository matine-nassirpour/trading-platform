from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable

from quantum.application.ports.outbound.transaction.unit_of_work_state import (
    UnitOfWorkState,
)


@runtime_checkable
class UnitOfWork(Protocol, AbstractContextManager["UnitOfWork"]):
    """
    Explicit transactional boundary.

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
    - after_commit() is valid only before COMMITTED/ROLLED_BACK/DISPOSED.
    - __exit__ must rollback if still ACTIVE and an exception occurred.
    - __exit__ must dispose resources exactly once.
    """

    @property
    def state(self) -> UnitOfWorkState:
        raise NotImplementedError

    def commit(self) -> None:
        raise NotImplementedError

    def rollback(self) -> None:
        raise NotImplementedError

    def after_commit(self, callback: Callable[[], None]) -> None:
        """
        Register callback executed only after a successful commit.

        Must fail if UnitOfWork is already committed, rolled back, or disposed.
        """
        raise NotImplementedError
