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
    reason_code: DecisionAuthorizationReasonCode | None

    def _validate(self) -> None:
        if not isinstance(self.status, DecisionAuthorizationStatus):
            raise InvariantViolation("status must be DecisionAuthorizationStatus")

        if self.reason_code is not None and not isinstance(
            self.reason_code, DecisionAuthorizationReasonCode
        ):
            raise InvariantViolation(
                "reason_code must be DecisionAuthorizationReasonCode"
            )

        if self.status.is_authorized() and self.reason_code is not None:
            raise InvariantViolation("Authorized result must not define reason_code")

        if self.status.is_rejected() and self.reason_code is None:
            raise InvariantViolation("Rejected result must define reason_code")

    # --- Semantic helpers -----------------------------------------------------

    def is_authorized(self) -> bool:
        return self.status.is_authorized()

    def is_rejected(self) -> bool:
        return self.status.is_rejected()

    # --- Canonical factories --------------------------------------------------

    @classmethod
    def authorized(cls) -> DecisionAuthorizationResult:
        return cls(
            status=DecisionAuthorizationStatus.authorized(),
            reason_code=None,
        )

    @classmethod
    def rejected(
        cls,
        *,
        reason_code: DecisionAuthorizationReasonCode,
    ) -> DecisionAuthorizationResult:
        return cls(
            status=DecisionAuthorizationStatus.rejected(),
            reason_code=reason_code,
        )
