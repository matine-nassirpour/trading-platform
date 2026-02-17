from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.identifiers.order_id import OrderId


@dataclass(frozen=True, slots=True)
class CancelOrderCommand(BaseCommand):
    order_id: OrderId
