from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.governance.decision_policy_evaluator import (
    DecisionPolicyEvaluator,
)
from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity


class DecisionEvaluationService:
    """
    Pure orchestration service for decision authorization.
    """

    @staticmethod
    def evaluate(
        *,
        policy: DecisionPolicy,
        decision: DecisionIdentity,
        context: TradingContext,
    ) -> DecisionPolicyResult:

        return DecisionPolicyEvaluator.evaluate(
            policy=policy,
            decision=decision,
            context=context,
        )
