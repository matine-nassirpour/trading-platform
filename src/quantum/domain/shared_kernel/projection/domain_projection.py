from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.projection.projection_cursor import ProjectionCursor
from quantum.domain.shared_kernel.projection.projection_state import ProjectionState

S = TypeVar("S", bound=ProjectionState)


class DomainProjection(ABC, Generic[S]):
    """
    Canonical interface for all domain projections.

    A projection:
    - consumes domain events
    - produces a derived immutable state
    - is deterministic
    """

    @abstractmethod
    def initial_state(self) -> S:
        """
        Returns the canonical initial state.
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, state: S, event: BaseEvent) -> S:
        """
        Applies a single domain event to the projection state.

        MUST be:
        - pure
        - deterministic
        - side-effect free
        """
        raise NotImplementedError

    def project(
        self,
        *,
        events: Iterable[BaseEvent],
        cursor: ProjectionCursor | None = None,
    ) -> tuple[S, ProjectionCursor]:
        """
        Projects a sequence of events into a derived state.
        """

        state = self.initial_state()
        last_cursor = cursor or ProjectionCursor.initial()

        for event in events:
            state = self.apply(state, event)
            last_cursor = ProjectionCursor(last_processed_at=event.occurred_at)

        return state, last_cursor
