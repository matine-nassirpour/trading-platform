from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.shared_kernel.value_objects.price import Price


@dataclass(frozen=True)
class ClosePositionCommand:
    position_id: PositionId
    exit_price: Price
