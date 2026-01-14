from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.projection.projection_cursor import ProjectionCursor
from quantum.domain.shared_kernel.projection.projection_error import ProjectionError

S = TypeVar("S")


class DomainProjection(ABC, Generic[S]):
    """
    Audit-grade domain projection.

    A DomainProjection:
    - Is part of the domain layer
    - Encodes event → state semantics
    - Is deterministic
    - Has no side effects
    - Is fully replayable
    """

    # --- Internal Guarantees --------------------------------------------------

    @staticmethod
    def _assert_sequential(envelope: EventEnvelope, expected_sequence: int) -> None:
        seq = envelope.sequence.value

        if seq != expected_sequence:
            raise ProjectionError(
                f"Event sequence violation: expected {expected_sequence}, got {seq}"
            )

    @staticmethod
    def _advance_cursor(envelope: EventEnvelope) -> ProjectionCursor:
        return ProjectionCursor(
            last_event_id=envelope.id,
            last_sequence=envelope.sequence,
        )

    # --- Semantic contract ----------------------------------------------------

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

    # --- Full Replay ----------------------------------------------------------

    def replay(self, events: Iterable[EventEnvelope]) -> tuple[S, ProjectionCursor]:
        """
        Rebuilds the projection state from genesis by replaying
        the entire event stream.

        This is the ONLY correct way to rebuild from scratch.
        """

        state = self.initial_state()
        cursor = ProjectionCursor.initial()

        expected_sequence = cursor.last_sequence.value + 1

        for envelope in events:
            self._assert_sequential(envelope, expected_sequence)

            state = self.apply(state, envelope.event)
            cursor = self._advance_cursor(envelope)

            expected_sequence += 1

        return state, cursor

    # --- Incremental Projection -----------------------------------------------

    def project_incremental(
        self,
        *,
        state: S,
        cursor: ProjectionCursor,
        events: Iterable[EventEnvelope],
    ) -> tuple[S, ProjectionCursor]:
        """
        Continues a projection from a known (state, cursor) pair.

        This is the ONLY correct way to apply events incrementally.
        """

        if not isinstance(cursor, ProjectionCursor):
            raise ProjectionError(
                "project_incremental requires a valid ProjectionCursor"
            )

        expected_sequence = cursor.last_sequence.value + 1

        for envelope in events:
            self._assert_sequential(envelope, expected_sequence)

            state = self.apply(state, envelope.event)
            cursor = self._advance_cursor(envelope)

            expected_sequence += 1

        return state, cursor
