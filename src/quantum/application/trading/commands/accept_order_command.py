from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.trading.order.aggregate import OrderId


@dataclass(frozen=True, slots=True)
class AcceptOrderCommand(BaseCommand):
    """
    Command: mark an acknowledged order as accepted by the broker/execution venue.
    """

    order_id: OrderId
