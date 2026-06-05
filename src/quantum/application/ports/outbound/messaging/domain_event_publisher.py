from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


@runtime_checkable
class DomainEventPublisher(Protocol):
    """
    Outbound port for publishing already-recorded domain events.

    Responsibility:
    - Publish events outside the application core.
    - No subscription.
    - No handler registration.
    - No dispatch orchestration.

    Typical implementations:
    - in-memory publisher
    - outbox relay
    - Kafka/NATS/ZeroMQ adapter
    - internal async transport adapter
    """

    async def publish(
        self,
        events: Sequence[RecordedEventEnvelope],
    ) -> None:
        """
        Publish recorded domain events.

        Contract:
        - Events are already persisted.
        - Publication must not mutate domain/application state.
        - Delivery semantics are infrastructure-defined and documented.
        """
        ...
