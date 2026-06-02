from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.event_sourcing.events.actor_id import ActorId
from quantum.domain.trading.order.aggregate import OrderId


@dataclass(frozen=True, slots=True)
class SubmitOrderCommand(BaseCommand):
    """
    Command: mark a created order as submitted.
    """

    order_id: OrderId
    submitted_by: ActorId
