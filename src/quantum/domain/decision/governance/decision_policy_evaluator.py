from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
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
    ) -> DecisionAuthorizationReasonCode | None:
        if decision.strategy_id != policy.strategy_id:
            return DecisionAuthorizationReasonCode.strategy_not_authorized()

        if context.market_regime not in policy.allowed_regimes:
            return DecisionAuthorizationReasonCode.market_regime_not_allowed()

        return None
