from quantum.domain.decision.authorization.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.authorization.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.authorization.decision_policy import DecisionPolicy
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


class DecisionPolicyEvaluator(DomainService):
    """
    Domain Service responsible for evaluating DecisionPolicy.

    HARD RULES:
    - Pure
    - Deterministic
    - No side effects
    - No runtime assumptions

    Domain responsibility:
        "Is this decision authorized under this policy?"
    """

    __slots__ = ()

    @staticmethod
    def evaluate(
        *,
        policy: DecisionPolicy,
        decision: DecisionIdentity,
        context: TradingContext,
        at: EpochMs,
    ) -> DecisionAuthorizationResult:

        # Strategy mismatch
        if decision.strategy_id != policy.strategy_id:
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_not_authorized()
            )

        if not policy.validity.is_valid_at(at):
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.policy_not_valid()
            )

        # Market regime not allowed
        if context.market_regime not in policy.allowed_regimes:
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.market_regime_not_allowed()
            )

        # Authorized
        return DecisionAuthorizationResult.authorized()
