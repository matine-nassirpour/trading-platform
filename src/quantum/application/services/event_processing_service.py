from collections.abc import Iterable
from typing import Protocol

from quantum.application.factories.event_envelope_factory import EventEnvelopeFactory
from quantum.application.ports.outbound.domain_event_publisher import EventPublisher
from quantum.application.ports.outbound.event_store import EventStore
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class SequenceProvider(Protocol):
    def next_sequence(self) -> EventSequence: ...


class EventProcessingService:
    """
    Canonical application service that converts DOMAIN events
    into APPLICATION event envelopes and persists/publishes them.
    """

    def __init__(
        self,
        *,
        event_store: EventStore,
        publisher: EventPublisher,
        sequence_provider: SequenceProvider,
    ) -> None:
        self._event_store = event_store
        self._publisher = publisher
        self._sequence_provider = sequence_provider

    def process(
        self,
        *,
        events: Iterable[BaseEvent],
        actor: ActorId,
        correlation: CorrelationId,
        causation: CausationId,
    ) -> list[EventEnvelope]:

        envelopes: list[EventEnvelope] = []

        for event in events:
            sequence = self._sequence_provider.next_sequence()

            envelope = EventEnvelopeFactory.create(
                event=event,
                sequence=sequence,
                actor=actor,
                correlation=correlation,
                causation=causation,
            )

            envelopes.append(envelope)

        self._event_store.append(envelopes)

        for env in envelopes:
            self._publisher.publish(env)

        return envelopes
