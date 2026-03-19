from dataclasses import dataclass

from quantum.domain.market.regime.market_regime import MarketRegime
from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.identity.strategy_id import StrategyId
from quantum.domain.shared_kernel.temporal.temporal_validity import TemporalValidity


@dataclass(frozen=True, slots=True)
class DecisionPolicy(ValueObject):
    """
    Canonical Decision Authorization policy.

    This object answers ONE and only ONE question:
        "Was this trading decision AUTHORIZED at this time?"

    This is:
    - NOT a signal
    - NOT a risk rule
    - NOT a sizing mechanism
    - A GOVERNANCE CONTRACT

    Audit meaning:
    - If a decision breaches a policy, the decision is INVALID,
      regardless of profitability or execution correctness.
    """

    policy_id: str

    strategy_id: StrategyId
    allowed_regimes: frozenset[MarketRegime]

    validity: TemporalValidity

    def _validate(self) -> None:
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise InvariantViolation("DecisionPolicy requires a non-empty policy_id")

        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("DecisionPolicy requires a StrategyId")

        if not isinstance(self.allowed_regimes, frozenset):
            raise InvariantViolation("allowed_regimes must be a frozenset")

        if not self.allowed_regimes:
            raise InvariantViolation("DecisionPolicy must allow at least one regime")

        for regime in self.allowed_regimes:
            if not isinstance(regime, MarketRegime):
                raise InvariantViolation("Invalid MarketRegime in allowed_regimes")

        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("DecisionPolicy requires TemporalValidity")
