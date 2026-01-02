from typing import Protocol, runtime_checkable

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)


@runtime_checkable
class IntegrationEventPublisher(Protocol):
    def publish(self, events: tuple[IntegrationEvent, ...]) -> None:
        raise NotImplementedError
