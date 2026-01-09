from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


@dataclass(frozen=True)
class PositionClosedEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position.closed"
    event_version: ClassVar[int] = 1

    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    exit_price: Price
    realized_pnl: RealizedPnL
