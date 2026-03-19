from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.actor_id import ActorId
from quantum.domain.shared_kernel.event_sourcing.events.causation_id import CausationId
from quantum.domain.shared_kernel.event_sourcing.events.correlation_id import (
    CorrelationId,
)


@dataclass(frozen=True, slots=True)
class ApplicationEventContext:
    """
    Immutable causal context propagated across the entire application layer.

    Guarantees:
    - Perfect traceability
    - Deterministic event lineage
    - No accidental correlation break
    - Audit-grade causal chain integrity

    This object MUST be passed explicitly through all application flows.
    """

    correlation_id: CorrelationId
    causation_id: CausationId
    actor_id: ActorId

    @staticmethod
    def root(
        *,
        correlation_id: CorrelationId,
        actor_id: ActorId,
    ) -> ApplicationEventContext:
        """
        Create root context for new command entrypoint.
        """
        return ApplicationEventContext(
            correlation_id=correlation_id,
            causation_id=CausationId.root(),
            actor_id=actor_id,
        )

    def next(self, *, causation_id: CausationId) -> ApplicationEventContext:
        """
        Create child context for downstream events.
        """
        return ApplicationEventContext(
            correlation_id=self.correlation_id,
            causation_id=causation_id,
            actor_id=self.actor_id,
        )
