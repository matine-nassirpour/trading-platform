from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.trading.order.aggregate import OrderId


@dataclass(frozen=True, slots=True)
class ExpireOrderCommand(BaseCommand):
    """
    Command: expire an active order.
    """

    order_id: OrderId
