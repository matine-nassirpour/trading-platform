from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.application.trading.integration_events.base.integration_event_envelope import (
    IntegrationEventEnvelope,
)


@runtime_checkable
class IntegrationEventBus(Protocol):
    """
    Dedicated outbound port for publishing Integration Events.

    Guarantees:
    - Transport abstraction
    - Infrastructure independence
    - Deterministic delivery contract
    """

    @abstractmethod
    def publish(self, events: list[IntegrationEventEnvelope]) -> None:
        """
        Publish integration events.

        Must guarantee:
        - at-least-once delivery
        - deterministic order preservation
        """
        raise NotImplementedError
