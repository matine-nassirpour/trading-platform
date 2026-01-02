from dataclasses import dataclass

from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.market.price import Price


@dataclass(frozen=True)
class ClosePositionCommand:
    position_id: PositionId
    exit_price: Price
