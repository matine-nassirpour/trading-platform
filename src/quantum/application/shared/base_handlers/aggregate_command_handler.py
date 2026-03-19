from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from quantum.application.ports.outbound.transaction.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.transaction.unit_of_work import UnitOfWork
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.shared.commands.base_command import BaseCommand
from quantum.application.shared.errors.application_error import (
    AggregateNotFoundError,
    ConcurrencyError,
    DomainExecutionError,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.shared.eventing.event_enveloper import (
    ApplicationEventEnveloper,
)
from quantum.application.shared.eventing.event_sourced_repository import (
    EventSourcedRepository,
)
from quantum.domain.shared_kernel.ddd.entities.aggregate_state import AggregateState
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.foundation.errors.domain_error import DomainError
from quantum.domain.shared_kernel.identity.aggregate_id import AggregateId

C = TypeVar("C", bound=BaseCommand)
R = TypeVar("R")  # Result
ID = TypeVar("ID", bound=AggregateId)
S = TypeVar("S", bound=AggregateState)
A = TypeVar("A", bound=EventSourcedAggregateRoot)


class AggregateCommandHandler(ABC, Generic[C, R, ID, S, A]):
    """
    Strict event-sourced aggregate mutation handler.

    Guarantees:
    - Typed aggregate identity throughout application core
    - Deterministic transaction boundary
    - Optimistic concurrency enforcement
    - Outbox pattern only
    """

    __slots__ = (
        "_repository",
        "_outbox",
        "_uow",
        "_enveloper",
        "_existence_policy",
    )

    def __init__(
        self,
        *,
        repository: EventSourcedRepository[ID, S, A],
        outbox: OutboxRepository,
        uow: UnitOfWork,
        enveloper: ApplicationEventEnveloper,
        existence_policy: AggregateExistencePolicy,
    ) -> None:
        self._repository = repository
        self._outbox = outbox
        self._uow = uow
        self._enveloper = enveloper
        self._existence_policy = existence_policy

    # --- Abstract contract for concrete handlers ------------------------------

    @abstractmethod
    def _aggregate_id(self, command: C) -> ID:
        """
        Return the typed aggregate identity targeted by this command.
        """
        raise NotImplementedError

    @abstractmethod
    def _context(self, command: C) -> ApplicationEventContext:
        """
        Extract application event context from command.
        """
        raise NotImplementedError

    @abstractmethod
    def _execute_domain(
        self,
        *,
        command: C,
        aggregate: A,
    ) -> tuple[Sequence[BaseEvent], R]:
        """
        Execute domain logic and return (domain_events, result).
        """
        raise NotImplementedError

    # --- Public entrypoint ------------------------------

    def _enforce_existence_policy(
        self,
        *,
        aggregate_id: ID,
        version: EventSequence,
    ) -> None:

        exists = not version.is_initial()

        if not exists and self._existence_policy == AggregateExistencePolicy.MUST_EXIST:
            raise AggregateNotFoundError(str(aggregate_id))

        if exists and self._existence_policy == AggregateExistencePolicy.MUST_NOT_EXIST:
            raise ConcurrencyError(f"Aggregate already exists for id '{aggregate_id}'")

    def handle(self, command: C) -> R:
        with self._uow:
            try:
                aggregate_id = self._aggregate_id(command)
                aggregate, expected_version = self._repository.load(
                    aggregate_id=aggregate_id
                )

                self._enforce_existence_policy(
                    aggregate_id=aggregate_id,
                    version=expected_version,
                )

                domain_events, result = self._execute_domain(
                    command=command,
                    aggregate=aggregate,
                )

                if not domain_events:
                    self._uow.commit()
                    return result

                context = self._context(command)

                pending = self._enveloper.envelope(
                    aggregate_id=aggregate_id,
                    events=domain_events,
                    context=context,
                )

                persisted = self._repository.save(
                    aggregate_id=aggregate_id,
                    expected_version=expected_version,
                    envelopes=pending,
                )

                self._outbox.add(persisted)

                self._uow.commit()
                return result

            except DomainError as error:
                self._uow.rollback()
                raise DomainExecutionError(error) from None

            except Exception:
                self._uow.rollback()
                raise
