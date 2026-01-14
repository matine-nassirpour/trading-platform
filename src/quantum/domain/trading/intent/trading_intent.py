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
from quantum.domain.trading.events.v1.order_intent_event import OrderIntentEvent
from quantum.domain.trading.events.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.trading.execution.order.order import Order
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


class TradingIntent(EventSourcedAggregateRoot):
    """
    Canonical event-sourced TradingIntent aggregate.
    Represents a governed trading decision envelope.
    """

    _intent_id: IntentId
    _symbol: Symbol
    _orders: dict[OrderId, Order]
    _submitted: bool

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def create(
        *,
        intent_id: IntentId,
        symbol: Symbol,
        occurred_at: EpochMs,
    ) -> TradingIntent:
        intent = TradingIntent()

        intent._raise(
            OrderIntentEvent(
                intent_id=intent_id,
                symbol=symbol,
            )
        )

        return intent

    # --- Commands -------------------------------------------------------------

    def submit(self, *, client_order_id: str) -> None:
        if self._submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        self._raise(
            OrderSubmitEvent(
                intent_id=self._intent_id,
                client_order_id=client_order_id,
                symbol=self._symbol,
            )
        )

    def attach_order(self, *, order: Order) -> None:
        if not self._submitted:
            raise InvalidStateTransition("Cannot attach order before submission")

        if order.order_id in self._orders:
            raise InvariantViolation("Duplicate OrderId in TradingIntent")

        self._raise(
            OrderCreatedEvent(
                intent_id=self._intent_id,
                order_id=order.order_id,
                symbol=self._symbol,
                order_type=order.order_type,
                side=order.side,
                volume=order.requested_volume,
            )
        )

    # --- Event application ----------------------------------------------------

    def _apply_tradingintentcreatedevent(self, event: OrderIntentEvent) -> None:
        self._intent_id = event.intent_id
        self._symbol = event.symbol
        self._orders = {}
        self._submitted = False

    def _apply_ordersubmitevent(self, event: OrderSubmitEvent) -> None:
        self._submitted = True

    def _apply_ordercreatedevent(self, event: OrderCreatedEvent) -> None:
        # Structural linkage only — Order owns its own lifecycle
        self._orders[event.order_id] = Order.rehydrate_from_events([])

    # --- Derived properties ---------------------------------------------------

    @property
    def intent_id(self) -> IntentId:
        return self._intent_id

    @property
    def symbol(self) -> Symbol:
        return self._symbol

    @property
    def is_submitted(self) -> bool:
        return self._submitted

    @property
    def orders(self) -> dict[OrderId, Order]:
        return dict(self._orders)

    # --- Aggregate invariants -------------------------------------------------

    def _validate_state(self) -> None:
        if not isinstance(self._intent_id, IntentId):
            raise InvariantViolation("IntentId missing")

        if not isinstance(self._symbol, Symbol):
            raise InvariantViolation("Symbol missing")

        if not isinstance(self._orders, dict):
            raise InvariantViolation("Orders container corrupted")

        if not isinstance(self._submitted, bool):
            raise InvariantViolation("Invalid submission flag")
