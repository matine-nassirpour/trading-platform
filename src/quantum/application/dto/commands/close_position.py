from dataclasses import dataclass

from quantum.domain.shared.value_objects.price import Price
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


@dataclass(frozen=True)
class ClosePositionCommand:
    position_id: PositionId
    exit_price: Price
