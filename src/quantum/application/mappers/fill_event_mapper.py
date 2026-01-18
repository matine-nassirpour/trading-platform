from quantum.application.integration_events.broker.order_filled_event import (
    OrderFilledEvent,
)
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.execution.settlement.execution_cost import ExecutionCost


class FillIntegrationEventMapper:

    @staticmethod
    def from_fill(
        *,
        intent_id,
        order_id,
        execution_fill: ExecutionFill,
        execution_cost: ExecutionCost | None = None,
    ) -> OrderFilledEvent:

        commission = execution_cost.fee if execution_cost is not None else None

        return OrderFilledEvent(
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
