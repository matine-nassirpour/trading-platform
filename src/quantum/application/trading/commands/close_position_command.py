from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.modeling.monetary.money_context import MoneyContext
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.identifiers.broker_position_ref import BrokerPositionRef


@dataclass(frozen=True, slots=True)
class ClosePositionCommand(BaseCommand):
    broker_position_ref: BrokerPositionRef
    exit_price: Price
    context: MoneyContext
