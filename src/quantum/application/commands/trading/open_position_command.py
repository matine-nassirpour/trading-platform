from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class OpenPositionCommand:
    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
