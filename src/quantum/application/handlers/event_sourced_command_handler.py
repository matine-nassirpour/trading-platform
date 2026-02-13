from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.errors.application_error import (
    ConcurrencyError,
    DomainExecutionError,
    NotFoundError,
)
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.repositories.event_sourced_repository import (
    EventSourcedRepository,
)
from quantum.application.ports.outbound.repositories.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope

C = TypeVar("C")  # Command type
R = TypeVar("R")  # Result type
A = TypeVar("A")  # Aggregate type


class EventSourcedCommandHandler(ABC, Generic[C, R, A]):
    """
    Pure orchestration layer.

    Responsibilities:
    - Transaction boundary
    - Aggregate existence enforcement
    - Delegation to domain logic
    - Persistence via repository
    - Outbox coordination
    """

    def __init__(
        self,
        *,
        repository: EventSourcedRepository[A],
        outbox: OutboxRepository,
        publisher: EventBusPort,
        uow: UnitOfWork,
        require_existing: bool,
    ) -> None:
        self._repository = repository
        self._outbox = outbox
        self._publisher = publisher
        self._uow = uow
        self._require_existing = require_existing

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

    # --- Core deterministic execution template --------------------------------

    def _execute(self, command: C) -> tuple[R, list[EventEnvelope]]:
        stream_id = self._stream_id(command)

        try:
            aggregate, expected_version = self._repository.load(stream_id)

            if self._require_existing and aggregate is None:
                raise NotFoundError(f"Aggregate not found: {stream_id}")

            domain_events, result = self._execute_domain(
                command=command,
                aggregate=aggregate,
            )

            if not domain_events:
                return result, []

            persisted = self._repository.save(
                stream_id=stream_id,
                expected_version=expected_version,
                domain_events=domain_events,
            )

            self._outbox.add(persisted)

            return result, persisted

        except DomainError as error:
            raise DomainExecutionError(error) from None

    # --- Public entrypoint ------------------------------

    def handle(self, command: C) -> R:
        """
        Execute a command inside a strict transactional boundary.
        """

        with self._uow:
            try:
                result, events_to_publish = self._execute(command)

                # Register post-commit publication
                self._uow.after_commit(
                    lambda: self._publisher.publish(events_to_publish)
                )

                self._uow.commit()
                return result

            except ConcurrencyError:
                self._uow.rollback()
                raise

            except Exception:
                self._uow.rollback()
                raise
