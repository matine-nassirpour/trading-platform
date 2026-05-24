from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.event_sourcing.events.actor_id import ActorId
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.cancellation.order_cancellation_origin import (
    OrderCancellationOrigin,
)
from quantum.domain.trading.order.cancellation.order_cancellation_reason import (
    OrderCancellationReason,
)


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent(FactEvent):
    """
    Emitted when an order is cancelled.

    Audit meaning:
    - WHO initiated or reported the cancellation
    - WHY the order was cancelled
    - WHERE the cancellation originated
    - WHEN the cancellation happened in business time
    """

    event_name: ClassVar[str] = "trading.order.cancelled"
    event_version: ClassVar[int] = 1

    broker_order_ref: BrokerOrderRef

    cancelled_by: ActorId
    reason: OrderCancellationReason
    origin: OrderCancellationOrigin
    cancelled_at: EpochMs

    comment: str | None = None

    def _validate_payload(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("broker_order_ref", self.broker_order_ref, BrokerOrderRef),
            ("cancelled_by", self.cancelled_by, ActorId),
            ("reason", self.reason, OrderCancellationReason),
            ("origin", self.origin, OrderCancellationOrigin),
            ("cancelled_at", self.cancelled_at, EpochMs),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"OrderCancelledEvent.{field_name} invalid")

        if self.comment is not None:
            if not isinstance(self.comment, str):
                raise InvariantViolation("OrderCancelledEvent.comment must be a string")

            if not self.comment.strip():
                raise InvariantViolation(
                    "OrderCancelledEvent.comment must not be blank"
                )
