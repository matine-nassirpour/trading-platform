from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.event_sourcing.events.actor_id import ActorId
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.trading.order.aggregate import OrderId
from quantum.domain.trading.order.cancellation.order_cancellation_origin import (
    OrderCancellationOrigin,
)
from quantum.domain.trading.order.cancellation.order_cancellation_reason import (
    OrderCancellationReason,
)


@dataclass(frozen=True, slots=True)
class CancelOrderCommand(BaseCommand):
    """
    Command: cancel an active order.
    """

    order_id: OrderId
    cancelled_by: ActorId
    reason: OrderCancellationReason
    origin: OrderCancellationOrigin
    cancelled_at: EpochMs
    comment: str | None = None
