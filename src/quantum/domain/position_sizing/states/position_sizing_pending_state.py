from dataclasses import dataclass

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.position_sizing.states.position_sizing_state_base import (
    PositionSizingStateBase,
)
from quantum.domain.position_sizing.value_objects.sizing_allocation import (
    SizingAllocation,
)
from quantum.domain.position_sizing.value_objects.sizing_equity import SizingEquity
from quantum.domain.position_sizing.value_objects.sizing_rounding_policy import (
    SizingRoundingPolicy,
)
from quantum.domain.position_sizing.value_objects.stop_distance import StopDistance
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class PositionSizingPendingState(PositionSizingStateBase):
    decision_id: DecisionId
    strategy_id: StrategyId
    symbol: Symbol
    allocation: SizingAllocation
    equity: SizingEquity
    stop_distance: StopDistance
    instrument: InstrumentSpec
    reference_price: ReferencePrice
    rounding_policy: SizingRoundingPolicy
    requested_at: EpochMs

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation("Pending PositionSizing cannot be initial")

        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("decision_id", self.decision_id, DecisionId),
            ("strategy_id", self.strategy_id, StrategyId),
            ("symbol", self.symbol, Symbol),
            ("allocation", self.allocation, SizingAllocation),
            ("equity", self.equity, SizingEquity),
            ("stop_distance", self.stop_distance, StopDistance),
            ("instrument", self.instrument, InstrumentSpec),
            ("reference_price", self.reference_price, ReferencePrice),
            ("rounding_policy", self.rounding_policy, SizingRoundingPolicy),
            ("requested_at", self.requested_at, EpochMs),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(
                    f"PositionSizingPendingState.{field_name} invalid"
                )
