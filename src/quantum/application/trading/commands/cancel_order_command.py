from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.trading.identifiers.broker_order_ref import BrokerOrderRef


@dataclass(frozen=True, slots=True)
class CancelOrderCommand(BaseCommand):
    broker_order_ref: BrokerOrderRef
