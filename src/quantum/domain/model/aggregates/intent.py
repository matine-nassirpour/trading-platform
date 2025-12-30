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

    Canonical invariants:
    - submitted == False  ⇒ orders == ()
    - submitted == True   ⇒ orders != ()
    - OrderId must be unique within the aggregate
    - Symbol is owned by the aggregate, not by individual orders
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
        volume: PositiveVolume,
        at: EpochMs,
        sizing_model: str | None = None,
    ) -> TradingIntent:
        """
        Creates an Order inside a submitted TradingIntent.

        Rules:
        - Intent MUST be submitted
        - Orders are immutable entities
        - Each creation emits domain events
        """
        if not self.submitted:
            raise InvalidStateTransition(
                "Cannot create Order before TradingIntent submission"
            )

        order = Order(
            order_id=order_id,
            requested_volume=volume,
            filled_volume=NonNegativeVolume.zero(),
            status=OrderStatus.PENDING,
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
