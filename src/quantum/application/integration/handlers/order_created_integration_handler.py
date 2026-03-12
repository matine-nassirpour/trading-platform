from quantum.application.integration.handlers.integration_event_handler import (
    IntegrationEventHandler,
)
from quantum.application.trading.integration_events.broker.order_acknowledged_event import (
    OrderAcknowledgedEvent,
)
from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.trading.events.v1.order.order_created_event import OrderCreatedEvent


class OrderCreatedIntegrationHandler(IntegrationEventHandler):

    def _map(self, envelope: RecordedEventEnvelope) -> OrderAcknowledgedEvent:

        event = envelope.event

        if not isinstance(event, OrderCreatedEvent):
            raise TypeError("Unexpected event type")

        return OrderAcknowledgedEvent(
            intent_id=event.intent_id,
            broker_order_id=event.broker_order_id,
            symbol=event.symbol,
        )
