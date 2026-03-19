from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.event_sourcing.projections.projection_cursor import (
    ProjectionCursor,
)
from quantum.domain.shared_kernel.foundation.errors.projection_error import (
    ProjectionError,
)

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
    def _assert_sequential(
        envelope: RecordedEventEnvelope, expected: EventSequence
    ) -> None:
        if not isinstance(expected, EventSequence):
            raise ProjectionError("Expected sequence must be an EventSequence")

        actual = envelope.sequence

        if not isinstance(actual, EventSequence):
            raise ProjectionError("Envelope.sequence must be an EventSequence")

        if actual.value != expected.value:
            raise ProjectionError(
                f"EventSequence violation: expected {expected.value}, got {actual.value}"
            )

    @staticmethod
    def _advance_cursor(envelope: RecordedEventEnvelope) -> ProjectionCursor:
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

    def replay(
        self, events: Iterable[RecordedEventEnvelope]
    ) -> tuple[S, ProjectionCursor]:
        """
        Rebuilds the projection state from genesis by replaying
        the entire event stream.
        """

        state = self.initial_state()
        cursor = ProjectionCursor.initial()

        expected = cursor.last_sequence.next()

        for envelope in events:
            self._assert_sequential(envelope, expected)

            state = self.apply(state, envelope.event)
            cursor = self._advance_cursor(envelope)

            expected = expected.next()

        return state, cursor

    # --- Incremental Projection -----------------------------------------------

    def project_incremental(
        self,
        *,
        state: S,
        cursor: ProjectionCursor,
        events: Iterable[RecordedEventEnvelope],
    ) -> tuple[S, ProjectionCursor]:
        """
        Continues a projection from a known (state, cursor) pair.
        """

        if not isinstance(cursor, ProjectionCursor):
            raise ProjectionError(
                "project_incremental requires a valid ProjectionCursor"
            )

        expected = cursor.last_sequence.next()

        for envelope in events:
            self._assert_sequential(envelope, expected)

            state = self.apply(state, envelope.event)
            cursor = self._advance_cursor(envelope)

            expected = expected.next()

        return state, cursor
