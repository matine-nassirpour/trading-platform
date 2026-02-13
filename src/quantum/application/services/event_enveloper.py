from collections.abc import Iterable

from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class ApplicationEventEnveloper:
    """
    Responsible for wrapping domain BaseEvent into EventEnvelope
    for stateless process handlers.

    Guarantees:
    - Metadata completeness
    - Deterministic timestamping
    - No sequence ownership (sequence assigned by store if needed)
    """

    def __init__(
        self,
        *,
        clock: Clock,
        ids: IdGenerator,
        actor: str,
    ) -> None:
        self._clock = clock
        self._ids = ids
        self._actor = ActorId(actor)

    def envelope(
        self,
        *,
        events: Iterable[BaseEvent],
        correlation_id: CorrelationId | None = None,
        causation_id: CausationId | None = None,
    ) -> list[EventEnvelope]:

        now = self._clock.now_epoch_ms()
        correlation_id = correlation_id or self._ids.new_correlation_id()
        causation_id = causation_id or CausationId.root()

        envelopes: list[EventEnvelope] = []

        for event in events:
            envelopes.append(
                EventEnvelope(
                    id=self._ids.new_event_id(),
                    sequence=EventSequence.initial(),
                    occurred_at=now,
                    recorded_at=now,
                    event=event,
                    metadata=EventMetadata(
                        actor_id=self._actor,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                    ),
                )
            )

        return envelopes
