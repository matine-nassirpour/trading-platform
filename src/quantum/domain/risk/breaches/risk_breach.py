from abc import ABC
from dataclasses import dataclass

from quantum.domain.risk.limits.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskBreach(ValueObject, ABC):
    """
    Algebraic root of all risk breaches.

    HARD GUARANTEES:
    - This class is abstract
    - No generic (current, limit) typing is allowed here
    - Each concrete subtype fully encodes its invariant in its type
    """

    policy: RiskThresholdPolicy

    def _validate(self) -> None:
        if not isinstance(self.policy, RiskThresholdPolicy):
            raise InvariantViolation("RiskBreach.policy must be a RiskThresholdPolicy")
