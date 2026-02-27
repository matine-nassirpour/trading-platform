from collections.abc import Iterable

from quantum.application.ports.outbound.identity.id_generator import IdGenerator
from quantum.application.ports.outbound.time.clock import Clock
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.shared.eventing.pending_event_envelope import (
    PendingEventEnvelope,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata


class ApplicationEventEnveloper:
    """
    Responsible for wrapping domain BaseEvent into EventEnvelope
    for stateless process handlers.

    Creates EventEnvelope WITHOUT sequence. Sequence is assigned ONLY by EventStore.

    Guarantees:
    - CorrelationId NEVER generated implicitly
    - CausationId ALWAYS derived from causal chain
    - Deterministic lineage
    """

    def __init__(
        self,
        *,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._clock = clock
        self._ids = ids

    def envelope(
        self,
        *,
        events: Iterable[BaseEvent],
        context: ApplicationEventContext,
    ) -> list[PendingEventEnvelope]:

        now = self._clock.now_epoch_ms()

        envelopes = [
            PendingEventEnvelope(
                id=self._ids.new_event_id(),
                occurred_at=now,
                recorded_at=now,
                event=event,
                metadata=EventMetadata(
                    actor_id=context.actor_id,
                    correlation_id=context.correlation_id,
                    causation_id=context.causation_id,
                ),
            )
            for event in events
        ]

        return envelopes
