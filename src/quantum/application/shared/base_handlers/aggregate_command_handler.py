from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.repositories.event_sourced_repository import (
    EventSourcedRepository,
)
from quantum.application.ports.outbound.transaction.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.transaction.unit_of_work import UnitOfWork
from quantum.application.shared.errors.application_error import (
    ConcurrencyError,
    DomainExecutionError,
    NotFoundError,
)
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent

C = TypeVar("C")  # Command
R = TypeVar("R")  # Result
A = TypeVar("A")  # Aggregate


class AggregateCommandHandler(ABC, Generic[C, R, A]):
    """
    Strict event-sourced aggregate mutation handler.

    Guarantees:
    - Deterministic transaction boundary
    - Optimistic concurrency enforcement
    - No async inside application core
    - Outbox pattern only
    """

    def __init__(
        self,
        *,
        repository: EventSourcedRepository[A],
        outbox: OutboxRepository,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._outbox = outbox
        self._uow = uow

    # --- Abstract contract for concrete handlers ------------------------------

    @abstractmethod
    def _stream_id(self, command: C) -> str:
        """
        Return the event stream identifier for the aggregate.
        """
        raise NotImplementedError

    @abstractmethod
    def _execute_domain(
        self,
        *,
        command: C,
        aggregate: A | None,
    ) -> tuple[Iterable[BaseEvent], R]:
        """
        Execute domain logic and return (events, result).
        """
        raise NotImplementedError

    # --- Public entrypoint ------------------------------

    def handle(self, command: C) -> R:
        with self._uow:
            try:
                stream_id = self._stream_id(command)

                aggregate, expected_version = self._repository.load(stream_id)

                if aggregate is None:
                    raise NotFoundError(f"Aggregate not found: {stream_id}")

                domain_events, result = self._execute_domain(
                    command=command,
                    aggregate=aggregate,
                )

                if domain_events:
                    persisted = self._repository.save(
                        stream_id=stream_id,
                        expected_version=expected_version,
                        domain_events=domain_events,
                    )

                    self._outbox.add(persisted)

                self._uow.commit()
                return result

            except DomainError as error:
                self._uow.rollback()
                raise DomainExecutionError(error) from None

            except ConcurrencyError:
                self._uow.rollback()
                raise

            except Exception:
                self._uow.rollback()
                raise
