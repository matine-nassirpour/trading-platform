from quantum.application.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.application.integration_events.base.integration_event_envelope import (
    IntegrationEventEnvelope,
)
from quantum.application.integration_events.base.integration_headers import (
    IntegrationHeaders,
)
from quantum.application.ports.outbound.clock import Clock
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


class IntegrationEventMapper:
    """
    Converts Domain EventEnvelope -> IntegrationEventEnvelope.
    """

    def __init__(self, *, clock: Clock) -> None:
        self._clock = clock

    def map(
        self,
        *,
        domain_envelope: EventEnvelope,
        integration_event: IntegrationEvent,
        source: str,
        tenant: str | None = None,
        environment: str | None = None,
    ) -> IntegrationEventEnvelope:

        headers = IntegrationHeaders(
            message_id=str(domain_envelope.id.value),
            event_name=integration_event.event_name,
            event_version=integration_event.event_version,
            correlation_id=domain_envelope.metadata.correlation_id,
            causation_id=domain_envelope.metadata.causation_id,
            actor_id=domain_envelope.metadata.actor_id,
            source=source,
            tenant=tenant,
            environment=environment,
        )

        return IntegrationEventEnvelope.create(
            payload=integration_event,
            headers=headers,
            occurred_at=domain_envelope.occurred_at,
            published_at=self._clock.now_epoch_ms(),
        )
