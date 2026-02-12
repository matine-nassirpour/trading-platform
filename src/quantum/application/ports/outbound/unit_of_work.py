from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable


@runtime_checkable
class UnitOfWork(Protocol, AbstractContextManager["UnitOfWork"]):
    """
    Transaction boundary.

    Intended usage:
        with uow:
            ...
            uow.commit()

    Infrastructure decides what commit means (db tx, outbox flush, etc.).
    """

    def commit(self) -> None:
        raise NotImplementedError

    def rollback(self) -> None:
        raise NotImplementedError

    def after_commit(self, callback: Callable[[], None]) -> None:
        """
        Register a callback executed only if commit succeeds.
        """
        raise NotImplementedError
