from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from quantum.application.ports.outbound.transaction.unit_of_work_factory import (
    UnitOfWorkFactory,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.shared.base_handlers.domain_event_batch_policy import (
    DomainEventBatchPolicy,
)
from quantum.application.shared.base_handlers.empty_event_policy import EmptyEventPolicy
from quantum.application.shared.commands.base_command import BaseCommand
from quantum.application.shared.errors.application_error import (
    AggregateNotFoundError,
    ApplicationInvariantViolationError,
    ConcurrencyError,
    DomainExecutionError,
    DuplicateCommandError,
    EmptyDomainEventError,
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
from quantum.application.shared.eventing.stream_name_resolver import StreamNameResolver
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.state.aggregate_state import (
    AggregateState,
)
from quantum.domain.shared_kernel.foundation.errors.domain_error import DomainError
from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId

C = TypeVar("C", bound=BaseCommand)
R = TypeVar("R")  # Result
ID = TypeVar("ID", bound=AggregateId)
S = TypeVar("S", bound=AggregateState)
A = TypeVar("A", bound=EventSourcedAggregateRoot[Any, Any])


class AggregateCommandHandler(ABC, Generic[C, R, ID, S, A]):
    """
    Strict event-sourced aggregate mutation handler.

    Guarantees:
    - Typed aggregate identity throughout application core.
    - Fresh UnitOfWork per command execution.
    - Deterministic transaction boundary.
    - Optimistic concurrency enforcement.
    - Outbox pattern only.
    """

    __slots__ = (
        "_aggregate_type",
        "_stream_resolver",
        "_uow_factory",
        "_enveloper",
        "_existence_policy",
        "_empty_event_policy",
        "_event_batch_policy",
    )

    def __init__(
        self,
        *,
        aggregate_type: type[A],
        stream_resolver: StreamNameResolver[ID],
        uow_factory: UnitOfWorkFactory,
        enveloper: ApplicationEventEnveloper,
        existence_policy: AggregateExistencePolicy,
        empty_event_policy: EmptyEventPolicy = EmptyEventPolicy.FORBID,
        event_batch_policy: DomainEventBatchPolicy | None = None,
    ) -> None:
        self._aggregate_type = aggregate_type
        self._stream_resolver = stream_resolver
        self._uow_factory = uow_factory
        self._enveloper = enveloper
        self._existence_policy = existence_policy
        self._empty_event_policy = empty_event_policy
        self._event_batch_policy = event_batch_policy or DomainEventBatchPolicy()

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
    async def _execute_domain(
        self,
        *,
        command: C,
        aggregate: A,
    ) -> tuple[Sequence[BaseEvent], R]:
        """
        Execute domain logic and return (domain_events, result).

        May await application ports before delegating to the domain.
        Must not contain domain decision logic.
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

    def _enforce_empty_event_policy(self, command: C) -> None:
        if self._empty_event_policy is EmptyEventPolicy.ALLOW_NOOP:
            return

        raise EmptyDomainEventError(
            f"Command '{command.__class__.__name__}' produced no domain events "
            "inside an event-sourced aggregate mutation handler"
        )

    async def handle(self, command: C) -> R:
        try:
            async with self._uow_factory.create() as uow:
                reserved = await uow.command_deduplication.reserve(command.command_id)

                if not reserved:
                    raise DuplicateCommandError(command.command_id)

                aggregate_id = self._aggregate_id(command)

                repository = EventSourcedRepository[ID, S, A](
                    store=uow.event_store,
                    aggregate_type=self._aggregate_type,
                    stream_resolver=self._stream_resolver,
                )

                aggregate, expected_version = await repository.load(
                    aggregate_id=aggregate_id,
                )

                self._enforce_existence_policy(
                    aggregate_id=aggregate_id,
                    version=expected_version,
                )

                domain_events_sequence, result = await self._execute_domain(
                    command=command,
                    aggregate=aggregate,
                )

                domain_events = list(domain_events_sequence)

                if not domain_events:
                    self._enforce_empty_event_policy(command)
                    await uow.commit()
                    return result

                self._event_batch_policy.validate(
                    command_name=command.__class__.__name__,
                    events=domain_events,
                )

                pending = await self._enveloper.envelope(
                    aggregate_id=aggregate_id,
                    events=domain_events,
                    context=self._context(command),
                )

                persisted = await repository.save(
                    aggregate_id=aggregate_id,
                    expected_version=expected_version,
                    envelopes=pending,
                )

                await uow.outbox.add(persisted)

                await uow.commit()
                return result

            raise ApplicationInvariantViolationError(
                "Unreachable code reached after UnitOfWork context exit"
            )

        except DomainError as error:
            raise DomainExecutionError(error) from None
