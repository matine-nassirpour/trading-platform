from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class PositionClosedEvent(FactEvent):
    event_name: ClassVar[str] = "trading.position.closed"
    event_version: ClassVar[int] = 1

    position_id: PositionId
    side: PositionSide
    volume: PositiveVolume
    exit_price: Price
    realized_pnl: RealizedPnL
