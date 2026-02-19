from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.governance.decision_authorization_status import (
    DecisionAuthorizationStatus,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DecisionAuthorizationResult(ValueObject):
    """
    Canonical authorization result.
    """

    status: DecisionAuthorizationStatus
    reason_code: DecisionAuthorizationReasonCode
    reason: str

    def _validate(self) -> None:
        if not isinstance(self.status, DecisionAuthorizationStatus):
            raise InvariantViolation("Invalid DecisionAuthorizationStatus")

        if not isinstance(self.reason_code, DecisionAuthorizationReasonCode):
            raise InvariantViolation("Invalid DecisionAuthorizationReasonCode")

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise InvariantViolation("DecisionAuthorizationResult requires reason")

        if self.status.is_authorized():
            if self.reason_code != DecisionAuthorizationReasonCode.authorized():
                raise InvariantViolation(
                    "Authorized status requires authorized reason_code"
                )

        if self.status.is_rejected():
            if self.reason_code == DecisionAuthorizationReasonCode.authorized():
                raise InvariantViolation(
                    "Rejected status cannot use authorized reason_code"
                )

    def is_authorized(self) -> bool:
        return self.status.is_authorized()

    def is_rejected(self) -> bool:
        return self.status.is_rejected()

    @staticmethod
    def authorized(reason: str) -> DecisionAuthorizationResult:
        return DecisionAuthorizationResult(
            status=DecisionAuthorizationStatus.authorized(),
            reason_code=DecisionAuthorizationReasonCode.authorized(),
            reason=reason,
        )

    @staticmethod
    def rejected(
        *,
        reason_code: DecisionAuthorizationReasonCode,
        reason: str,
    ) -> DecisionAuthorizationResult:
        return DecisionAuthorizationResult(
            status=DecisionAuthorizationStatus.rejected(),
            reason_code=reason_code,
            reason=reason,
        )
