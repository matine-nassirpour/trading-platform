from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from quantum.application.commands.command_result import CommandResult
from quantum.application.errors.application_error import ApplicationError
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.unit_of_work import UnitOfWork

C = TypeVar("C")  # Command type
R = TypeVar("R")  # Result type


class CommandHandler(ABC, Generic[C, R]):
    """
    Base transactional template for all application command handlers.

    Architectural guarantees:
    - Strict transactional boundary (UnitOfWork)
    - Automatic rollback on failure
    - No duplicated commit logic
    - No event publication responsibility (Outbox pattern)
    - Infrastructure-agnostic
    - Deterministic execution model
    """

    def __init__(
        self,
        *,
        outbox: OutboxRepository,
        uow: UnitOfWork,
        store: EventStore,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._outbox = outbox
        self._uow = uow
        self._store = store
        self._clock = clock
        self._ids = ids

    # --- To be implemented by subclasses --------------------------------------

    @abstractmethod
    def _execute(self, command: C) -> R:
        """
        Execute command logic inside an active transaction.
        """
        raise NotImplementedError

    # --- To be implemented by subclasses --------------------------------------

    def handle(self, command: C) -> CommandResult[R]:
        """
        Template method enforcing strict transaction lifecycle.
        """

        try:
            with self._uow:
                result: R = self._execute(command)
                self._uow.commit()

            return CommandResult(value=result, success=True)

        except ApplicationError:
            # Already boundary-safe → propagate
            raise

        except Exception:
            # Rollback occurs implicitly if commit was not called.
            # We deliberately do not swallow unexpected exceptions.
            raise
