from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from quantum.application.ports.outbound.transaction.unit_of_work import UnitOfWork
from quantum.application.ports.outbound.transaction.unit_of_work_state import (
    UnitOfWorkState,
)
from quantum.application.shared.errors.application_error import ApplicationError


class UnitOfWorkStateError(ApplicationError):
    """
    Raised when UnitOfWork state machine is violated.
    """


class BaseUnitOfWork(UnitOfWork, ABC):
    """
    Reusable state-machine implementation for infrastructure UnitOfWork adapters.

    Infrastructure subclasses implement:
    - _begin()
    - _commit()
    - _rollback()
    - _dispose()

    Strict rule:
    - UnitOfWork never executes post-commit application callbacks.
    - Post-commit effects must be implemented through a durable outbox relay.
    """

    __slots__ = ("_state",)

    def __init__(self) -> None:
        self._state = UnitOfWorkState.NEW

    @property
    def state(self) -> UnitOfWorkState:
        return self._state

    def __enter__(self) -> Self:
        if self._state is not UnitOfWorkState.NEW:
            raise UnitOfWorkStateError(
                f"Cannot enter UnitOfWork from state {self._state.name}"
            )

        self._begin()
        self._state = UnitOfWorkState.ACTIVE
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        try:
            if self._state is UnitOfWorkState.ACTIVE:
                self.rollback()
        finally:
            self._dispose_once()

        return False

    def commit(self) -> None:
        if self._state is not UnitOfWorkState.ACTIVE:
            raise UnitOfWorkStateError(
                f"Cannot commit UnitOfWork from state {self._state.name}"
            )

        self._commit()
        self._state = UnitOfWorkState.COMMITTED

    def rollback(self) -> None:
        if self._state is not UnitOfWorkState.ACTIVE:
            raise UnitOfWorkStateError(
                f"Cannot rollback UnitOfWork from state {self._state.name}"
            )

        self._rollback()
        self._state = UnitOfWorkState.ROLLED_BACK

    def _dispose_once(self) -> None:
        if self._state is UnitOfWorkState.DISPOSED:
            return

        self._dispose()
        self._state = UnitOfWorkState.DISPOSED

    @abstractmethod
    def _begin(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _dispose(self) -> None:
        raise NotImplementedError
