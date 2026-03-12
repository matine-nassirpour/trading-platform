from collections import defaultdict

from quantum.application.integration.handlers.integration_event_handler import (
    IntegrationEventHandler,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


class IntegrationEventRegistry:
    """
    Registry mapping DomainEvent → IntegrationEventHandler
    """

    def __init__(self) -> None:
        self._handlers: dict[type[BaseEvent], list[IntegrationEventHandler]] = (
            defaultdict(list)
        )

    def register(
        self,
        event_type: type[BaseEvent],
        handler: IntegrationEventHandler,
    ) -> None:

        self._handlers[event_type].append(handler)

    def dispatch(self, envelope: RecordedEventEnvelope) -> None:

        handlers = self._handlers.get(type(envelope.event), [])

        for handler in handlers:
            handler.handle(envelope)
