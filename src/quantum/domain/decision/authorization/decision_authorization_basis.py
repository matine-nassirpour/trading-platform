from dataclasses import dataclass

from quantum.domain.decision.authorization.decision_policy_id import DecisionPolicyId
from quantum.domain.decision.authorization.strategy_lifecycle_state import (
    StrategyLifecycleState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DecisionAuthorizationBasis(ValueObject):
    """
    Canonical immutable snapshot of the governance basis used to authorize
    or reject a trade candidate.

    This object records the normative context actually used at decision time.
    """

    policy_id: DecisionPolicyId
    lifecycle_state: StrategyLifecycleState

    def _validate_semantics(self) -> None:
        if not isinstance(self.policy_id, DecisionPolicyId):
            raise InvariantViolation(
                "DecisionAuthorizationBasis requires a DecisionPolicyId"
            )

        if not isinstance(self.lifecycle_state, StrategyLifecycleState):
            raise InvariantViolation(
                "DecisionAuthorizationBasis requires a StrategyLifecycleState"
            )
