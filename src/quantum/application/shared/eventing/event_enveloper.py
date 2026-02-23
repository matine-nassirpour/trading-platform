from collections.abc import Iterable

from quantum.application.ports.outbound.identity.id_generator import IdGenerator
from quantum.application.ports.outbound.time.clock import Clock
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class ApplicationEventEnveloper:
    """
    Responsible for wrapping domain BaseEvent into EventEnvelope
    for stateless process handlers.

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
    ) -> list[EventEnvelope]:

        now = self._clock.now_epoch_ms()

        envelopes = [
            EventEnvelope(
                id=self._ids.new_event_id(),
                sequence=EventSequence.initial(),
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
