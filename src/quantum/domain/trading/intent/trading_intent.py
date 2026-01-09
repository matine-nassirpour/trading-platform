from __future__ import annotations

from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.events.v1.order_created_event import OrderCreatedEvent
from quantum.domain.trading.events.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.trading.execution.order.order import Order
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


class TradingIntent(EventSourcedAggregateRoot):
    """
    Canonical event-sourced TradingIntent aggregate.
    """

    _intent_id: IntentId
    _symbol: Symbol
    _side: PositionSide
    _orders: tuple[Order, ...] = ()
    _submitted: bool = False

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def create(
        *,
        intent_id: IntentId,
        symbol: Symbol,
    ) -> TradingIntent:
        intent = TradingIntent()
        intent._intent_id = intent_id
        intent._symbol = symbol
        intent._orders = {}
        intent._submitted = False
        return intent

    # --- Commands -------------------------------------------------------------

    def submit(self, *, at: EpochMs, client_order_id: str) -> None:
        if self._submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        self._raise(
            OrderSubmitEvent(
                occurred_at=at,
                intent_id=self._intent_id,
                client_order_id=client_order_id,
                symbol=self._symbol,
            )
        )

    def create_order(
        self,
        *,
        order: Order,
        at: EpochMs,
    ) -> None:
        if not self._submitted:
            raise InvalidStateTransition("Cannot create order before submission")

        if order._order_id in self._orders:
            raise InvariantViolation("Duplicate OrderId")

        self._raise(
            OrderCreatedEvent(
                occurred_at=at,
                intent_id=self._intent_id,
                order_id=order._order_id,
                symbol=self._symbol,
                volume=order._requested_volume,
            )
        )

        self._orders[order._order_id] = order

    # --- Event application ----------------------------------------------------

    def _apply_ordersubmitevent(self, event: OrderSubmitEvent) -> None:
        self._submitted = True

    def _apply_ordercreatedevent(self, event: OrderCreatedEvent) -> None:
        pass  # structural event, Order owns its own state

    # --- Aggregate invariants -------------------------------------------------

    def _validate_state(self) -> None:
        if not isinstance(self._intent_id, IntentId):
            raise InvariantViolation("IntentId missing")

        if not isinstance(self._symbol, Symbol):
            raise InvariantViolation("Symbol missing")

        if not isinstance(self._submitted, bool):
            raise InvariantViolation("Invalid submission flag")

        if not isinstance(self._orders, dict):
            raise InvariantViolation("Orders container corrupted")
