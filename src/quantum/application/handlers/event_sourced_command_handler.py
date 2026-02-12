from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.errors.application_error import (
    ConcurrencyError,
    DomainExecutionError,
)
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.repositories.event_sourced_repository import (
    EventSourcedRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence

C = TypeVar("C")  # Command type
R = TypeVar("R")  # Result type
A = TypeVar("A")  # Aggregate type


class EventSourcedCommandHandler(ABC, Generic[C, R, A]):
    """
    Industry-grade event-sourced transactional command handler.

    Guarantees:
    - Centralized optimistic concurrency control
    - Centralized event persistence
    - Strict causation chain propagation
    - Deterministic envelope creation
    - Zero duplication across handlers
    """

    _ACTOR = "system:application"

    def __init__(
        self,
        *,
        repository: EventSourcedRepository,
        outbox: OutboxRepository,
        uow: UnitOfWork,
        store: EventStore,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._repository = repository
        self._outbox = outbox
        self._uow = uow
        self._store = store
        self._clock = clock
        self._ids = ids

    # --- Public entrypoint ------------------------------

    def handle(self, command: C) -> R:
        """
        Execute a command inside a strict transactional boundary.

        Lifecycle:
            1. Load version
            2. Execute domain logic
            3. Persist events
            4. Store outbox
            5. Commit
        """

        with self._uow:
            try:
                result = self._execute(command)
                self._uow.commit()
                return result

            except ConcurrencyError:
                self._uow.rollback()
                raise

            except Exception:
                self._uow.rollback()
                raise

    # --- Abstract contract for concrete handlers ------------------------------

    @abstractmethod
    def _stream_id(self, command: C) -> str:
        """
        Return the event stream identifier for the aggregate.
        """
        raise NotImplementedError

    @abstractmethod
    def _load_aggregate(self, command: C) -> A | None:
        """
        Load aggregate instance (if existing).
        May return None for create operations.
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

    # --- Centralized persistence logic ----------------------------------------

    def _persist(
        self,
        *,
        stream_id: str,
        events: Iterable[BaseEvent],
        expected_version: EventSequence,
    ) -> None:

        correlation_id = self._ids.new_correlation_id()
        now = self._clock.now_epoch_ms()

        envelopes: list[EventEnvelope] = []

        for event in events:
            envelopes.append(
                EventEnvelope(
                    id=self._ids.new_event_id(),
                    sequence=EventSequence.initial(),
                    occurred_at=now,
                    recorded_at=now,
                    event=event,
                    metadata=EventMetadata(
                        actor_id=ActorId(self._ACTOR),
                        correlation_id=correlation_id,
                        causation_id=CausationId.root(),  # upgradeable later
                    ),
                )
            )

        persisted = self._store.append(
            stream_id=stream_id,
            events=envelopes,
            expected_version=expected_version,
        )

        self._outbox.add(persisted)

    # --- Core deterministic execution template --------------------------------

    def _execute(self, command: C) -> R:
        stream_id = self._stream_id(command)

        try:
            aggregate, expected_version = self._repository.load(stream_id)

            domain_events, result = self._execute_domain(
                command=command,
                aggregate=aggregate,
            )

            if not domain_events:
                return result

            self._persist(
                stream_id=stream_id,
                events=domain_events,
                expected_version=expected_version,
            )

            return result

        except DomainError as error:
            raise DomainExecutionError(error) from None
