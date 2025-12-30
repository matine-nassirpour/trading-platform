from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.events.trading.v1.order_created_event import OrderCreatedEvent
from quantum.domain.events.trading.v1.order_sizing_event import OrderSizingEvent
from quantum.domain.events.trading.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.entities.order import Order
from quantum.domain.model.exceptions.validation_exceptions import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import NonNegativeVolume, PositiveVolume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True)
class TradingIntent(AggregateRoot):
    """
    Aggregate Root representing a trading intent.

    Invariants:
    - submitted == False  => orders == ()
    - orders != ()        => submitted == True
    - order_id unique within orders
    """

    intent_id: IntentId
    symbol: Symbol
    orders: tuple[Order, ...] = ()
    submitted: bool = False

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        # orders container integrity
        if not isinstance(self.orders, tuple):
            raise InvariantViolation("Orders must be stored as an immutable tuple")

        # submission / orders coherence
        if not self.submitted and self.orders:
            raise InvariantViolation("Orders cannot exist before intent submission")

        if self.submitted and not isinstance(self.orders, tuple):
            raise InvariantViolation("Orders must be a tuple after submission")

        # uniqueness of OrderId
        order_ids = [o.order_id for o in self.orders]
        if len(order_ids) != len(set(order_ids)):
            raise InvariantViolation("Duplicate OrderId detected in TradingIntent")

    # --- Commands -------------------------------------------------------------

    def submit(self, at: EpochMs, client_order_id: str) -> TradingIntent:
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
        volume: PositiveVolume,
        at: EpochMs,
        sizing_model: str | None = None,
    ) -> TradingIntent:
        if not self.submitted:
            raise InvalidStateTransition("Cannot create order before submission")

        order = Order(
            order_id=order_id,
            requested_volume=volume,
            filled_volume=NonNegativeVolume.zero(),
            status=OrderStatus.PENDING,
        )

        intent = replace(self, orders=self.orders + (order,))

        events = []

        if sizing_model is not None:
            events.append(
                OrderSizingEvent(
                    occurred_at=at.to_datetime(),
                    intent_id=self.intent_id,
                    symbol=self.symbol,
                    volume=volume,
                    sizing_model=sizing_model,
                    decision_epoch_ms=at,
                )
            )

        events.append(
            OrderCreatedEvent(
                occurred_at=at.to_datetime(),
                intent_id=self.intent_id,
                order_id=order_id,
                symbol=self.symbol,
                volume=volume,
                decision_epoch_ms=at,
            )
        )

        for event in events:
            intent = intent._raise(event)

        return intent
