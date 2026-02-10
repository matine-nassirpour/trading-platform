from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.repositories.projection_repository import (
    ProjectionRepositoryPort,
)
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.projection.domain_projection import DomainProjection

S = TypeVar("S")


class ProjectionService(Generic[S]):
    """
    Application service orchestrating projection updates.
    """

    def __init__(
        self,
        projection: DomainProjection[S],
        repository: ProjectionRepositoryPort[S],
    ) -> None:
        self._projection = projection
        self._repository = repository

    def project(self, events: Iterable[EventEnvelope]) -> None:
        state, cursor = self._repository.load()

        new_state, new_cursor = self._projection.project_incremental(
            state=state,
            cursor=cursor,
            events=events,
        )

        self._repository.save(new_state, new_cursor)
