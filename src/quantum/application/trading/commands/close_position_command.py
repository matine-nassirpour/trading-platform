from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.value_objects.price import Price


@dataclass(frozen=True, slots=True)
class ClosePositionCommand(BaseCommand):
    position_id: PositionId
    exit_price: Price
    context: MoneyContext
