from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId


@dataclass(frozen=True, slots=True)
class RegisterOrderFillCommand(BaseCommand):
    broker_order_id: BrokerOrderId
    fill: ExecutionFill
