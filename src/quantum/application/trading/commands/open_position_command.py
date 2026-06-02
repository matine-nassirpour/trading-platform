from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef
from quantum.domain.trading.position.aggregate import PositionId


@dataclass(frozen=True, slots=True)
class OpenPositionCommand(BaseCommand):
    """
    Command: create and open a Position aggregate stream.
    """

    position_id: PositionId
    broker_position_ref: BrokerPositionRef
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
