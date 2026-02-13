from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.repositories.transactional_projection_repository import (
    TransactionalProjectionRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.projection.domain_projection import DomainProjection

S = TypeVar("S")


class TransactionalProjectionService(Generic[S]):
    """
    Guarantees:
    - Runs inside same UnitOfWork as event persistence
    - Crash-safe
    - Idempotent
    - Cursor monotonic enforcement
    """

    def __init__(
        self,
        *,
        projection: DomainProjection[S],
        repository: TransactionalProjectionRepository[S],
        uow: UnitOfWork,
    ) -> None:
        self._projection = projection
        self._repository = repository
        self._uow = uow

    def project(self, events: Iterable[EventEnvelope]) -> None:
        """
        Apply projection inside current UnitOfWork.

        Assumes caller already inside transaction.
        """

        state, cursor = self._repository.load()

        new_state, new_cursor = self._projection.project_incremental(
            state=state,
            cursor=cursor,
            events=events,
        )

        self._repository.save(
            state=new_state,
            cursor=new_cursor,
            applied_events=list(events),
        )
