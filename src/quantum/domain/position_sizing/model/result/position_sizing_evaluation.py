from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.position_sizing.model.policies.position_sizing_rejection_reason_code import (
    PositionSizingRejectionReasonCode,
)
from quantum.domain.position_sizing.model.result.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PositionSizingEvaluation(ValueObject):
    """
    Algebraic result of a sizing evaluation.

    Exactly one of:
    - result
    - rejection_reason
    must be present.
    """

    result: PositionSizingResult | None
    rejection_reason: PositionSizingRejectionReasonCode | None

    def _validate_semantics(self) -> None:
        if self.result is None and self.rejection_reason is None:
            raise InvariantViolation(
                "PositionSizingEvaluation must contain result or rejection_reason"
            )

        if self.result is not None and self.rejection_reason is not None:
            raise InvariantViolation(
                "PositionSizingEvaluation cannot contain both result and rejection_reason"
            )

        if self.result is not None and not isinstance(
            self.result, PositionSizingResult
        ):
            raise InvariantViolation("PositionSizingEvaluation.result invalid")

        if self.rejection_reason is not None and not isinstance(
            self.rejection_reason,
            PositionSizingRejectionReasonCode,
        ):
            raise InvariantViolation(
                "PositionSizingEvaluation.rejection_reason invalid"
            )

    def is_sized(self) -> bool:
        return self.result is not None

    def is_rejected(self) -> bool:
        return self.rejection_reason is not None

    @staticmethod
    def sized(result: PositionSizingResult) -> PositionSizingEvaluation:
        return PositionSizingEvaluation(result=result, rejection_reason=None)

    @staticmethod
    def rejected(
        reason: PositionSizingRejectionReasonCode,
    ) -> PositionSizingEvaluation:
        return PositionSizingEvaluation(result=None, rejection_reason=reason)
