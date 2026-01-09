from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.projection.projection_cursor import ProjectionCursor
from quantum.domain.shared_kernel.projection.projection_error import ProjectionError
from quantum.domain.shared_kernel.projection.projection_state import ProjectionState

S = TypeVar("S", bound=ProjectionState)


class DomainProjection(ABC, Generic[S]):
    """
    Audit-grade domain projection.

    Guarantees:
    - Strict event ordering
    - No gaps
    - No duplicates
    - Deterministic replay
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
        """
        raise NotImplementedError

    def project(
        self,
        *,
        events: Iterable[EventEnvelope],
        cursor: ProjectionCursor | None = None,
    ) -> tuple[S, ProjectionCursor]:

        state = self.initial_state()
        cursor = cursor or ProjectionCursor.initial()

        expected_sequence = cursor.last_sequence.value + 1

        for envelope in events:
            seq = envelope.sequence.value

            # HARD MONOTONICITY GUARANTEES
            if seq != expected_sequence:
                raise ProjectionError(
                    f"Event sequence violation: expected {expected_sequence}, got {seq}"
                )

            if seq <= cursor.last_sequence.value:
                raise ProjectionError("Duplicate or out-of-order event detected")

            # Apply event
            state = self.apply(state, envelope.event)

            cursor = ProjectionCursor(
                last_event_id=envelope.id,
                last_sequence=envelope.sequence,
            )

            expected_sequence += 1

        return state, cursor
