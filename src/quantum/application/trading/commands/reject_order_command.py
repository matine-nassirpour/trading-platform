from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.trading.execution.reports.execution_rejection import (
    ExecutionRejection,
)
from quantum.domain.trading.order.aggregate import OrderId


@dataclass(frozen=True, slots=True)
class RejectOrderCommand(BaseCommand):
    """
    Command: reject an active order with a canonical execution rejection payload.
    """

    order_id: OrderId
    rejection: ExecutionRejection
