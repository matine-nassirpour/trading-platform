from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.trading.order.aggregate import OrderId


@dataclass(frozen=True, slots=True)
class AcknowledgeOrderCommand(BaseCommand):
    """
    Command: mark a submitted order as acknowledged by the broker/execution venue.
    """

    order_id: OrderId
