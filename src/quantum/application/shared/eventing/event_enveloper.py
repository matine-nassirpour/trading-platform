from collections.abc import Sequence

from quantum.application.ports.outbound.identity.id_generator import IdGenerator
from quantum.application.ports.outbound.time.clock import Clock
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.shared.eventing.pending_event_envelope import (
    PendingEventEnvelope,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_metadata import (
    EventMetadata,
)
from quantum.domain.shared_kernel.identity.aggregate_id import AggregateId


class ApplicationEventEnveloper:
    """
    Wrap domain events into pending envelopes.

    Guarantees:
    - Aggregate identity is explicit
    - EventId is assigned before persistence
    - occurred_at is assigned by application time source
    - recorded_at and sequence remain EventStore responsibilities
    """

    __slots__ = ("_clock", "_ids")

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
        aggregate_id: AggregateId,
        events: Sequence[BaseEvent],
        context: ApplicationEventContext,
    ) -> list[PendingEventEnvelope]:
        now = self._clock.now_epoch_ms()

        return [
            PendingEventEnvelope(
                aggregate_id=aggregate_id,
                id=self._ids.new_event_id(),
                occurred_at=now,
                event=event,
                metadata=EventMetadata(
                    actor_id=context.actor_id,
                    correlation_id=context.correlation_id,
                    causation_id=context.causation_id,
                ),
            )
            for event in events
        ]
