from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.common.events.risk_event import RiskEvent
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.risk.sizing.position_sizing_id import PositionSizingId
from quantum.domain.risk.sizing.value_objects.sizing_rounding_policy import (
    SizingRoundingPolicy,
)
from quantum.domain.risk.sizing.value_objects.stop_distance import StopDistance
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class PositionSizingRequestedEvent(RiskEvent):
    event_name: ClassVar[str] = "risk.sizing.requested"
    event_version: ClassVar[int] = 1

    sizing_id: PositionSizingId
    decision_id: DecisionId
    strategy_id: StrategyId
    symbol: Symbol
    allocation: CapitalAllocationIntent
    equity: Equity
    stop_distance: StopDistance
    instrument: InstrumentSpec
    reference_price: ReferencePrice
    rounding_policy: SizingRoundingPolicy
