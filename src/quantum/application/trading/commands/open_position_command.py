from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identifiers.broker_position_ref import BrokerPositionRef
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class OpenPositionCommand(BaseCommand):
    broker_position_ref: BrokerPositionRef
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
