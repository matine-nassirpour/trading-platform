from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.repositories.transactional_projection_repository import (
    TransactionalProjectionRepository,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.event_sourcing.projections.domain_projection import (
    DomainProjection,
)

S = TypeVar("S")


class TransactionalProjectionService(Generic[S]):
    """
    Transaction-bound projection service.

    Guarantees:
    - Does not create or own transactions.
    - Must be called inside an already active UnitOfWork.
    - Projection persistence is delegated to a transaction-bound repository.
    """

    __slots__ = ("_projection", "_repository")

    def __init__(
        self,
        *,
        projection: DomainProjection[S],
        repository: TransactionalProjectionRepository[S],
    ) -> None:
        self._projection = projection
        self._repository = repository

    async def project(self, events: Iterable[RecordedEventEnvelope]) -> None:
        """
        Assumes caller already inside transaction.
        """

        events_list = list(events)

        state, cursor = await self._repository.load()

        new_state, new_cursor = self._projection.project_incremental(
            state=state,
            cursor=cursor,
            events=events_list,
        )

        await self._repository.save(
            state=new_state,
            cursor=new_cursor,
            applied_events=events_list,
        )
