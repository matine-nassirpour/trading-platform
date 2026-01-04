from quantum.application.integration_events.broker.order_fill_event import (
    OrderFillEvent,
)
from quantum.domain.execution.value_objects.execution_cost import ExecutionCost
from quantum.domain.execution.value_objects.execution_fill import ExecutionFill


class FillIntegrationEventMapper:

    @staticmethod
    def from_fill(
        *,
        intent_id,
        order_id,
        execution_fill: ExecutionFill,
        execution_cost: ExecutionCost | None = None,
    ) -> OrderFillEvent:

        commission = execution_cost.fee if execution_cost is not None else None

        return OrderFillEvent(
            occurred_at=execution_fill.executed_at,
            intent_id=intent_id,
            order_id=order_id,
            deal_id=None,
            symbol=None,
            price=execution_fill.price,
            volume=execution_fill.volume,
            commission=commission,
            swap=None,
            profit=None,
            deal_entry=None,
            reason=None,
            fill_epoch_ms=execution_fill.executed_at,
            partial=True,
        )
