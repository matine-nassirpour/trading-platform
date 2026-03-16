from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base.fact_event import FactEvent
from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.shared_kernel.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class PositionOpenedEvent(FactEvent):
    event_name: ClassVar[str] = "trading.position.opened"
    event_version: ClassVar[int] = 1

    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
