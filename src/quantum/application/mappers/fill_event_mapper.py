from quantum.application.integration_events.broker.order_fill_event import (
    OrderFillEvent,
)
from quantum.domain.execution.value_objects.fill import Fill


class FillIntegrationEventMapper:

    @staticmethod
    def from_fill(
        *,
        intent_id,
        order_id,
        fill: Fill,
    ) -> OrderFillEvent:
        return OrderFillEvent(
            occurred_at=fill.executed_at.to_datetime(),
            intent_id=intent_id,
            order_id=order_id,
            deal_id=None,
            symbol=None,
            price=fill.price,
            volume=fill.volume,
            commission=fill.fee,
            swap=None,
            profit=None,
            deal_entry=None,
            reason=None,
            fill_epoch_ms=fill.executed_at,
            partial=True,
        )
