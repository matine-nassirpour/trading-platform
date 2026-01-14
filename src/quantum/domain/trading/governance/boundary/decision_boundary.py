from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.temporal.temporal_validity import TemporalValidity
from quantum.domain.trading.context.market_regime import MarketRegime
from quantum.domain.trading.decision.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class DecisionBoundary(ValueObject):
    """
    Canonical Decision Authorization Boundary.

    This object answers ONE and only ONE question:

        "Was this trading decision AUTHORIZED at this time?"

    This is:
    - NOT a signal
    - NOT a risk rule
    - NOT a sizing mechanism
    - A GOVERNANCE CONTRACT

    Audit meaning:
    - If a decision breaches a boundary, the decision is INVALID,
      regardless of profitability or execution correctness.
    """

    boundary_id: str

    strategy_id: StrategyId
    allowed_regimes: frozenset[MarketRegime]

    validity: TemporalValidity

    # Optional governance flags
    requires_human_approval: bool = False
    experimental: bool = False

    def _validate(self) -> None:
        if not isinstance(self.boundary_id, str) or not self.boundary_id.strip():
            raise InvariantViolation(
                "DecisionBoundary requires a non-empty boundary_id"
            )

        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("DecisionBoundary requires a StrategyId")

        if not isinstance(self.allowed_regimes, frozenset):
            raise InvariantViolation("allowed_regimes must be a frozenset")

        if not self.allowed_regimes:
            raise InvariantViolation("DecisionBoundary must allow at least one regime")

        for regime in self.allowed_regimes:
            if not isinstance(regime, MarketRegime):
                raise InvariantViolation("Invalid MarketRegime in allowed_regimes")

        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("DecisionBoundary requires TemporalValidity")
