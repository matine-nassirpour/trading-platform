from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.transaction.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.transaction.unit_of_work import UnitOfWork
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
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

    def _enforce_existence_policy(
        self,
        stream_id: str,
        aggregate: A | None,
    ) -> None:

        if (
            aggregate is None
            and self._existence_policy == AggregateExistencePolicy.MUST_EXIST
        ):
            raise AggregateNotFoundError(stream_id)

        if (
            aggregate is not None
            and self._existence_policy == AggregateExistencePolicy.MUST_NOT_EXIST
        ):
            raise ConcurrencyError(f"Aggregate already exists for stream '{stream_id}'")

    def handle(self, command: C) -> R:
        with self._uow:
            try:
                stream_id = self._stream_id(command)
                aggregate, expected_version = self._repository.load(stream_id)

                self._enforce_existence_policy(stream_id, aggregate)

                domain_events, result = self._execute_domain(
                    command=command,
                    aggregate=aggregate,
                )

                if domain_events:
                    context: ApplicationEventContext = command.context
                    envelopes = self._enveloper.envelope(
                        events=domain_events,
                        context=context,
                    )

                    persisted = self._repository.save(
                        stream_id=stream_id,
                        expected_version=expected_version,
                        envelopes=envelopes,
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
