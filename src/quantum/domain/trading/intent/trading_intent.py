from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.execution.value_objects.fill import Fill
from quantum.domain.shared.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared.primitives.aggregate_root import AggregateRoot
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.shared.value_objects.volume import PositiveVolume
from quantum.domain.trading.events.v1.order_created_event import OrderCreatedEvent
from quantum.domain.trading.events.v1.order_sizing_event import OrderSizingEvent
from quantum.domain.trading.events.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.trading.order.order import Order
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId
from quantum.domain.trading.value_objects.order.order_status import OrderStatus
from quantum.domain.trading.value_objects.order.order_type import OrderType
from quantum.domain.trading.value_objects.order.position_side import PositionSide


@dataclass(frozen=True)
class TradingIntent(AggregateRoot):
    """
    Aggregate Root representing a trading intent.

    Canonical invariants:
    - submitted == False  ⇒ orders == ()
    - submitted == True   ⇒ orders != ()
    - OrderId must be unique within the aggregate
    - Symbol is owned by the aggregate, not by individual orders
    """

    intent_id: IntentId
    symbol: Symbol
    side: PositionSide
    orders: tuple[Order, ...] = ()
    submitted: bool = False

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        # orders container integrity
        if not isinstance(self.orders, tuple):
            raise InvariantViolation("Orders must be stored as an immutable tuple")

        # submission ↔ orders coherence
        if not self.submitted and self.orders:
            raise InvariantViolation(
                "Orders cannot exist before TradingIntent submission"
            )

        if self.submitted and not self.orders:
            raise InvariantViolation(
                "Submitted TradingIntent must contain at least one Order"
            )

        # uniqueness of OrderId
        order_ids = [order.order_id for order in self.orders]
        if len(order_ids) != len(set(order_ids)):
            raise InvariantViolation("Duplicate OrderId detected within TradingIntent")

    # --- Commands -------------------------------------------------------------

    def submit(self, *, at: EpochMs, client_order_id: str) -> TradingIntent:
        """
        Submits the trading intent.

        Rules:
        - Can only be submitted once
        - Does not create orders
        - Orders must be created AFTER submission
        """
        if self.submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        event = OrderSubmitEvent(
            occurred_at=at.to_datetime(),
            intent_id=self.intent_id,
            client_order_id=client_order_id,
            symbol=self.symbol,
            request_epoch_ms=at,
        )

        return replace(self, submitted=True)._raise(event)

    def create_order(
        self,
        *,
        order_id: OrderId,
        order_type: OrderType,
        volume: PositiveVolume,
        at: EpochMs,
        sizing_model: str | None = None,
    ) -> TradingIntent:
        """
        Creates an Order inside a submitted TradingIntent.

        Rules:
        - Intent MUST be submitted
        - OrderType is explicit and immutable
        - PositionSide is inherited from the TradingIntent
        - Each Order has a unique OrderId within the aggregate
        - Order starts with zero filled volume
        """

        if not self.submitted:
            raise InvalidStateTransition(
                "Cannot create Order before TradingIntent submission"
            )

        if any(o.order_id == order_id for o in self.orders):
            raise InvariantViolation(f"Duplicate OrderId: {order_id}")

        order = Order(
            order_id=order_id,
            order_type=order_type,
            side=self.side,
            requested_volume=volume,
            fills=(),
            status=OrderStatus.pending(),
        )

        intent = replace(self, orders=self.orders + (order,))

        if sizing_model is not None:
            intent = intent._raise(
                OrderSizingEvent(
                    occurred_at=at.to_datetime(),
                    intent_id=self.intent_id,
                    symbol=self.symbol,
                    volume=volume,
                    sizing_model=sizing_model,
                    decision_epoch_ms=at,
                )
            )

        intent = intent._raise(
            OrderCreatedEvent(
                occurred_at=at.to_datetime(),
                intent_id=self.intent_id,
                order_id=order_id,
                symbol=self.symbol,
                volume=volume,
                decision_epoch_ms=at,
            )
        )

        return intent

    def register_fill(
        self,
        *,
        order_id: OrderId,
        fill: Fill,
    ) -> TradingIntent:
        """
        Registers a fill on one of the Orders belonging to this TradingIntent.

        Invariants:
        - Order must exist in the aggregate
        - Order must be fillable
        - All Order invariants are preserved
        """

        updated_orders = []
        found = False

        for order in self.orders:
            if order.order_id == order_id:
                updated_orders.append(order.register_fill(fill))
                found = True
            else:
                updated_orders.append(order)

        if not found:
            raise InvariantViolation(
                f"Order {order_id} not found in TradingIntent {self.intent_id}"
            )

        return replace(self, orders=tuple(updated_orders))
