from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.projection.projection_cursor import ProjectionCursor
from quantum.domain.shared_kernel.projection.projection_error import ProjectionError

S = TypeVar("S")


class DomainProjection(DomainObject, ABC, Generic[S]):
    """
    Audit-grade domain projection.

    A DomainProjection:
    - Is part of the domain layer
    - Encodes event → state semantics
    - Is deterministic
    - Has no side effects
    - Is fully replayable
    """

    # --- Architectural role ---------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.PROJECTION

    # --- Projection contract --------------------------------------------------

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

    # --- Projection engine --------------------------------------------------

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

            if seq != expected_sequence:
                raise ProjectionError(
                    f"Event sequence violation: expected {expected_sequence}, got {seq}"
                )

            state = self.apply(state, envelope.event)

            cursor = ProjectionCursor(
                last_event_id=envelope.id,
                last_sequence=envelope.sequence,
            )

            expected_sequence += 1

        return state, cursor
