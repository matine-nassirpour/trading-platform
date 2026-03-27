from quantum.domain.decision.authorization.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.authorization.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.authorization.strategy_lifecycle import StrategyLifecycle
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


class StrategyEligibilityPolicy(DomainService):
    """
    Domain Service evaluating whether a strategy is eligible
    to produce trading decisions.

    Formal domain question answered:
        "Is this strategy allowed to produce decisions at this time?"
    """

    __slots__ = ()

    @staticmethod
    def evaluate(
        *,
        decision: DecisionIdentity,
        lifecycle: StrategyLifecycle,
        at: EpochMs,
    ) -> DecisionAuthorizationResult:

        if lifecycle.strategy_id != decision.strategy_id:
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_not_authorized()
            )

        if not lifecycle.validity.is_valid_at(at):
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_lifecycle_invalid()
            )

        if not lifecycle.state.is_authorized():
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_not_authorized()
            )

        return DecisionAuthorizationResult.authorized()
