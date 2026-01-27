from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity


class DecisionPolicyEvaluator:
    """
    Canonical policy for evaluating Decision policies.

    HARD RULES:
    - Pure
    - Deterministic
    - No side effects
    - No runtime assumptions
    """

    @staticmethod
    def evaluate(
        *,
        policy: DecisionPolicy,
        decision: DecisionIdentity,
        context: TradingContext,
    ) -> DecisionPolicyResult:
        if decision.strategy_id != policy.strategy_id:
            return DecisionPolicyResult(
                authorized=False,
                reason="Strategy not authorized by this policy",
            )

        if context.market_regime not in policy.allowed_regimes:
            return DecisionPolicyResult(
                authorized=False,
                reason="Market regime not authorized by this policy",
            )

        return DecisionPolicyResult(
            authorized=True,
            reason="Decision authorized by policy",
        )
