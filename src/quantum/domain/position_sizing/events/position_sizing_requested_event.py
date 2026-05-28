from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.position_sizing.events.position_sizing_event import (
    PositionSizingEvent,
)
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId
from quantum.domain.position_sizing.value_objects.sizing_allocation import (
    SizingAllocation,
)
from quantum.domain.position_sizing.value_objects.sizing_equity import SizingEquity
from quantum.domain.position_sizing.value_objects.sizing_rounding_policy import (
    SizingRoundingPolicy,
)
from quantum.domain.position_sizing.value_objects.stop_distance import StopDistance
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class PositionSizingRequestedEvent(PositionSizingEvent):
    event_name: ClassVar[str] = "position_sizing.requested"
    event_version: ClassVar[int] = 1

    sizing_id: PositionSizingId
    decision_id: DecisionId
    strategy_id: StrategyId
    symbol: Symbol
    allocation: SizingAllocation
    equity: SizingEquity
    stop_distance: StopDistance
    instrument: InstrumentSpec
    reference_price: ReferencePrice
    rounding_policy: SizingRoundingPolicy
