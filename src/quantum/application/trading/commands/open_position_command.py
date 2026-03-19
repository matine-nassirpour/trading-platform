from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.monetary.price import Price
from quantum.domain.trading.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class OpenPositionCommand(BaseCommand):
    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
