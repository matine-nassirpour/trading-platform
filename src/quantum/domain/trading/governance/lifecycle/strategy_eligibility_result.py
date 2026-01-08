from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class StrategyEligibilityResult(ValueObject):
    """
    Result of a strategy eligibility evaluation.
    """

    eligible: bool
    reason: str

    def _validate(self) -> None:
        if not isinstance(self.eligible, bool):
            raise InvariantViolation("eligible must be a boolean")

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise InvariantViolation(
                "StrategyEligibilityResult requires a non-empty reason"
            )
