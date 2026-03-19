from abc import ABC, abstractmethod

from quantum.application.ports.outbound.messaging.integration_event_bus import (
    IntegrationEventBus,
)
from quantum.application.trading.integration_events.base.integration_event_mapper import (
    IntegrationEventMapper,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


class IntegrationEventHandler(ABC):
    """
    Base class responsible for converting Domain EventEnvelope
    into IntegrationEventEnvelope and publishing it.
    """

    def __init__(
        self,
        *,
        mapper: IntegrationEventMapper,
        bus: IntegrationEventBus,
    ) -> None:
        self._mapper = mapper
        self._bus = bus

    @abstractmethod
    def _map(self, domain_envelope: RecordedEventEnvelope):
        raise NotImplementedError

    def handle(self, domain_envelope: RecordedEventEnvelope) -> None:

        integration_event = self._map(domain_envelope)

        integration_envelope = self._mapper.map(
            domain_envelope=domain_envelope,
            integration_event=integration_event,
            source="quantum-platform",
        )

        self._bus.publish([integration_envelope])
