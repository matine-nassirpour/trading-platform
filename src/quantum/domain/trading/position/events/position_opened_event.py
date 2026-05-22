from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef


@dataclass(frozen=True, slots=True)
class PositionOpenedEvent(FactEvent):
    event_name: ClassVar[str] = "trading.position.opened"
    event_version: ClassVar[int] = 1

    broker_position_ref: BrokerPositionRef
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
