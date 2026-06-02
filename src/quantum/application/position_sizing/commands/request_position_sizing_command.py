from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.position_sizing.model.allocation.sizing_allocation import (
    SizingAllocation,
)
from quantum.domain.position_sizing.model.equity.sizing_equity import SizingEquity
from quantum.domain.position_sizing.model.policies.sizing_rounding_policy import (
    SizingRoundingPolicy,
)
from quantum.domain.position_sizing.model.volume.stop_distance import StopDistance
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class RequestPositionSizingCommand(BaseCommand):
    """
    Command: request a new position sizing evaluation.

    Application responsibility:
    - target the PositionSizing stream;
    - pass canonical domain inputs;
    - preserve causal context.

    Domain responsibility:
    - record the sizing request;
    - later evaluate the sizing using PositionSizer.
    """

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
