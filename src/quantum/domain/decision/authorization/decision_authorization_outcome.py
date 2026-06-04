from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.decision.authorization.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.authorization.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.authorization.decision_authorization_status import (
    DecisionAuthorizationStatus,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DecisionAuthorizationOutcome(ValueObject):
    """
    Canonical domain outcome of a TradingDecision authorization attempt.

    This is the domain-level semantic result.
    Application handlers must depend on this object, not on concrete event types.
    """

    result: DecisionAuthorizationResult

    def _validate_semantics(self) -> None:
        if not isinstance(self.result, DecisionAuthorizationResult):
            raise InvariantViolation(
                "DecisionAuthorizationOutcome requires DecisionAuthorizationResult"
            )

    @property
    def status(self) -> DecisionAuthorizationStatus:
        return self.result.status

    @property
    def reason_code(self) -> DecisionAuthorizationReasonCode | None:
        return self.result.reason_code

    def is_authorized(self) -> bool:
        return self.result.is_authorized()

    def is_rejected(self) -> bool:
        return self.result.is_rejected()

    @classmethod
    def authorized(cls) -> DecisionAuthorizationOutcome:
        return cls(result=DecisionAuthorizationResult.authorized())

    @classmethod
    def rejected(
        cls,
        *,
        reason_code: DecisionAuthorizationReasonCode,
    ) -> DecisionAuthorizationOutcome:
        return cls(result=DecisionAuthorizationResult.rejected(reason_code=reason_code))
